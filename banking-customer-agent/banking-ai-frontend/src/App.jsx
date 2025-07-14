import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { MessageSquare, Settings, Bot, Shield, TrendingUp } from 'lucide-react'
import ChatInterface from './components/ChatInterface'
import AdminDashboard from './components/AdminDashboard'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('chat')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Banking AI Agent</h1>
                <p className="text-sm text-gray-500">Intelligent Customer Service Platform</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                System Online
              </Badge>
              <Badge variant="outline">
                GPT-4o Powered
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Customer Chat
            </TabsTrigger>
            <TabsTrigger value="admin" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Admin Dashboard
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Chat Interface */}
              <div className="lg:col-span-3">
                <ChatInterface />
              </div>

              {/* Sidebar */}
              <div className="space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Features</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Shield className="w-4 h-4 text-blue-600" />
                      <span>Compliance Monitoring</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <TrendingUp className="w-4 h-4 text-green-600" />
                      <span>Self-Reflection & Learning</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Bot className="w-4 h-4 text-purple-600" />
                      <span>Advanced Planning</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <MessageSquare className="w-4 h-4 text-orange-600" />
                      <span>Context Memory</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Sample Queries</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm space-y-2">
                      <p className="text-gray-600 cursor-pointer hover:text-blue-600 transition-colors">
                        "What's my account balance?"
                      </p>
                      <p className="text-gray-600 cursor-pointer hover:text-blue-600 transition-colors">
                        "Show me my recent transactions"
                      </p>
                      <p className="text-gray-600 cursor-pointer hover:text-blue-600 transition-colors">
                        "I want to transfer $500 to savings"
                      </p>
                      <p className="text-gray-600 cursor-pointer hover:text-blue-600 transition-colors">
                        "Tell me about your credit cards"
                      </p>
                      <p className="text-gray-600 cursor-pointer hover:text-blue-600 transition-colors">
                        "Help me understand loan options"
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Banking Capabilities</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <Badge variant="outline" className="mr-2 mb-2">Account Management</Badge>
                      <Badge variant="outline" className="mr-2 mb-2">Transaction Processing</Badge>
                      <Badge variant="outline" className="mr-2 mb-2">Product Information</Badge>
                      <Badge variant="outline" className="mr-2 mb-2">Fraud Detection</Badge>
                      <Badge variant="outline" className="mr-2 mb-2">Compliance Checking</Badge>
                      <Badge variant="outline" className="mr-2 mb-2">Customer Support</Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="admin">
            <AdminDashboard />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Banking AI Agent - Powered by GPT-4o | Built for JP Morgan, Capital One, ABSA
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Demo Environment</span>
              <span>•</span>
              <span>Simulated Banking Data</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

