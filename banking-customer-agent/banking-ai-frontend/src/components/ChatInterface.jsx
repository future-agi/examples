import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Send, Bot, User, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: 'Hello! I\'m your Banking AI Assistant. How can I help you today?',
      timestamp: new Date(),
      confidence: 0.95,
      compliance: 'compliant'
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [customerId, setCustomerId] = useState('CUST001') // Demo customer
  const [sessionId] = useState(`session_${Date.now()}`)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: inputValue,
          customer_id: customerId,
          session_id: sessionId,
          context: {}
        })
      })

      const data = await response.json()

      if (data.success) {
        const botMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: data.response,
          timestamp: new Date(),
          confidence: data.confidence_score,
          compliance: data.compliance_status,
          planId: data.plan_id,
          executionTime: data.execution_time
        }

        setMessages(prev => [...prev, botMessage])
      } else {
        const errorMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: 'I apologize, but I encountered an error processing your request. Please try again.',
          timestamp: new Date(),
          confidence: 0.0,
          compliance: 'error'
        }

        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'I\'m having trouble connecting to the server. Please check your connection and try again.',
        timestamp: new Date(),
        confidence: 0.0,
        compliance: 'error'
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const getComplianceIcon = (compliance) => {
    switch (compliance) {
      case 'compliant':
        return <CheckCircle className="w-3 h-3 text-green-500" />
      case 'warning':
        return <AlertCircle className="w-3 h-3 text-yellow-500" />
      case 'violation':
        return <AlertCircle className="w-3 h-3 text-red-500" />
      default:
        return <Clock className="w-3 h-3 text-gray-500" />
    }
  }

  const getComplianceColor = (compliance) => {
    switch (compliance) {
      case 'compliant':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'violation':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* Header */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Bot className="w-6 h-6 text-blue-600" />
              Banking AI Assistant
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                Customer: {customerId}
              </Badge>
              <Badge variant="outline" className="text-xs">
                Session: {sessionId.slice(-8)}
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Messages */}
      <Card className="flex-1 flex flex-col">
        <CardContent className="flex-1 p-0">
          <ScrollArea className="h-[500px] p-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                  className={`flex gap-3 mb-4 ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.type === 'bot' && (
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-blue-600" />
                    </div>
                  )}
                  
                  <div className={`max-w-[70%] ${message.type === 'user' ? 'order-2' : ''}`}>
                    <div
                      className={`rounded-lg p-3 ${
                        message.type === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      
                      {message.type === 'bot' && (
                        <>
                          {message.confidence !== undefined && (
                            <Badge variant="outline" className="text-xs">
                              Confidence: {(message.confidence * 100).toFixed(0)}%
                            </Badge>
                          )}
                          
                          {message.compliance && (
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${getComplianceColor(message.compliance)}`}
                            >
                              {getComplianceIcon(message.compliance)}
                              <span className="ml-1 capitalize">{message.compliance}</span>
                            </Badge>
                          )}
                          
                          {message.executionTime && (
                            <Badge variant="outline" className="text-xs">
                              {message.executionTime.toFixed(2)}s
                            </Badge>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  {message.type === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 order-3">
                      <User className="w-4 h-4 text-gray-600" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 mb-4"
              >
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-blue-600" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-gray-500">Thinking...</span>
                  </div>
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </ScrollArea>
        </CardContent>

        {/* Input */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about your accounts, transactions, or banking services..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button 
              onClick={sendMessage} 
              disabled={!inputValue.trim() || isLoading}
              className="px-3"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send • This is a demo environment with simulated banking data
          </p>
        </div>
      </Card>
    </div>
  )
}

export default ChatInterface

