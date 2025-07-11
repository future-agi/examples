import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { 
  Activity, 
  Users, 
  MessageSquare, 
  Shield, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Brain,
  Settings
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'

const AdminDashboard = () => {
  const [systemStatus, setSystemStatus] = useState(null)
  const [qualityMetrics, setQualityMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  // Mock data for charts
  const conversationData = [
    { time: '00:00', conversations: 12, successful: 11 },
    { time: '04:00', conversations: 8, successful: 8 },
    { time: '08:00', conversations: 25, successful: 23 },
    { time: '12:00', conversations: 45, successful: 42 },
    { time: '16:00', conversations: 38, successful: 35 },
    { time: '20:00', conversations: 22, successful: 20 },
  ]

  const complianceData = [
    { name: 'Compliant', value: 85, color: '#10b981' },
    { name: 'Warning', value: 12, color: '#f59e0b' },
    { name: 'Violation', value: 3, color: '#ef4444' },
  ]

  const modulePerformance = [
    { module: 'Planning', performance: 92 },
    { module: 'RAG', performance: 88 },
    { module: 'Execution', performance: 95 },
    { module: 'Memory', performance: 90 },
    { module: 'Reflection', performance: 87 },
    { module: 'Compliance', performance: 96 },
  ]

  useEffect(() => {
    fetchSystemStatus()
    fetchQualityMetrics()
  }, [])

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/health')
      const data = await response.json()
      setSystemStatus(data)
    } catch (error) {
      console.error('Error fetching system status:', error)
      setSystemStatus({ status: 'error', message: 'Unable to connect to backend' })
    }
  }

  const fetchQualityMetrics = async () => {
    try {
      const response = await fetch('http://localhost:5000/analytics/quality')
      const data = await response.json()
      setQualityMetrics(data.quality_metrics)
    } catch (error) {
      console.error('Error fetching quality metrics:', error)
      setQualityMetrics(null)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100'
      case 'warning':
        return 'text-yellow-600 bg-yellow-100'
      case 'error':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4" />
      case 'error':
        return <AlertTriangle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-500">Banking AI Agent System Monitoring</p>
        </div>
        <Button onClick={() => { fetchSystemStatus(); fetchQualityMetrics(); }}>
          <Activity className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">System Status</p>
                <div className="flex items-center gap-2 mt-2">
                  {systemStatus && getStatusIcon(systemStatus.status)}
                  <Badge className={getStatusColor(systemStatus?.status || 'unknown')}>
                    {systemStatus?.status || 'Unknown'}
                  </Badge>
                </div>
              </div>
              <Activity className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Sessions</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">24</p>
              </div>
              <Users className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Conversations</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">1,247</p>
              </div>
              <MessageSquare className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Compliance Rate</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">96.2%</p>
              </div>
              <Shield className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
          <TabsTrigger value="modules">Modules</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Conversation Trends */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Conversation Trends (24h)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={conversationData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="conversations" stroke="#3b82f6" strokeWidth={2} />
                    <Line type="monotone" dataKey="successful" stroke="#10b981" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Compliance Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Compliance Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={complianceData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}%`}
                    >
                      {complianceData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Quality Metrics */}
          {qualityMetrics && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5" />
                  AI Quality Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-600">Average Confidence</p>
                    <div className="flex items-center gap-2">
                      <Progress value={qualityMetrics.average_confidence * 100} className="flex-1" />
                      <span className="text-sm font-medium">{(qualityMetrics.average_confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-600">Average Accuracy</p>
                    <div className="flex items-center gap-2">
                      <Progress value={qualityMetrics.average_accuracy * 100} className="flex-1" />
                      <span className="text-sm font-medium">{(qualityMetrics.average_accuracy * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-600">Completeness</p>
                    <div className="flex items-center gap-2">
                      <Progress value={qualityMetrics.average_completeness * 100} className="flex-1" />
                      <span className="text-sm font-medium">{(qualityMetrics.average_completeness * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-600">Clarity</p>
                    <div className="flex items-center gap-2">
                      <Progress value={qualityMetrics.average_clarity * 100} className="flex-1" />
                      <span className="text-sm font-medium">{(qualityMetrics.average_clarity * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Total Interactions: {qualityMetrics.total_interactions}</span>
                    <span className="text-gray-600">Escalation Rate: {(qualityMetrics.escalation_rate * 100).toFixed(1)}%</span>
                    <Badge variant="outline" className="capitalize">
                      Trend: {qualityMetrics.recent_trend}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Module Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={modulePerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="module" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="performance" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="compliance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Compliance Rules</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {['KYC Requirements', 'AML Monitoring', 'BSA Reporting', 'Privacy Protection', 'Fair Lending'].map((rule, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <span className="font-medium">{rule}</span>
                      <Badge className="bg-green-100 text-green-800">Active</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Compliance Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-3 border rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">High-value transaction detected</p>
                      <p className="text-xs text-gray-500">Customer CUST001 - $15,000 transfer</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 border rounded-lg">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">KYC verification completed</p>
                      <p className="text-xs text-gray-500">Customer CUST002 - Identity verified</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="modules" className="space-y-6">
          {systemStatus?.agent_status && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(systemStatus.agent_status).map(([moduleName, moduleData]) => (
                <Card key={moduleName}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 capitalize">
                      <Database className="w-5 h-5" />
                      {moduleName}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Status</span>
                        <Badge className={getStatusColor(moduleData.status)}>
                          {moduleData.status}
                        </Badge>
                      </div>
                      {moduleData.capabilities && (
                        <div>
                          <p className="text-sm text-gray-600 mb-2">Capabilities</p>
                          <div className="flex flex-wrap gap-1">
                            {moduleData.capabilities.slice(0, 3).map((capability, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {capability.replace(/_/g, ' ')}
                              </Badge>
                            ))}
                            {moduleData.capabilities.length > 3 && (
                              <Badge variant="outline" className="text-xs">
                                +{moduleData.capabilities.length - 3} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                System Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Model Temperature</label>
                    <input 
                      type="number" 
                      step="0.1" 
                      min="0" 
                      max="2" 
                      defaultValue="0.1"
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Max Tokens</label>
                    <input 
                      type="number" 
                      defaultValue="2000"
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Context Window (hours)</label>
                    <input 
                      type="number" 
                      defaultValue="24"
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Max Retrieval Docs</label>
                    <input 
                      type="number" 
                      defaultValue="10"
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                </div>
                <div className="pt-4">
                  <Button>Save Configuration</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AdminDashboard

