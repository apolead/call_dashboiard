'use client'

import { useState, useEffect } from 'react'
import Papa, { ParseResult, ParseError } from 'papaparse'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js'
import { Bar, Pie, Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
)

interface CallData {
  timestamp: string
  filename: string
  call_date: string
  call_time: string
  phone_number: string
  call_status: string
  agent_name: string
  estimated_duration_seconds: string
  file_size: string
  duration: string
  transcription: string
  summary: string
  intent: string
  sub_intent: string
  status: string
  processing_time: string
  error_message: string
  primary_disposition: string
  secondary_disposition: string
}

export default function Dashboard() {
  const [data, setData] = useState<CallData[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedIntent, setSelectedIntent] = useState('all')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/call_transcriptions.csv')
        const text = await response.text()
        
        Papa.parse(text, {
          header: true,
          complete: (results: Papa.ParseResult<CallData>) => {
            setData(results.data as CallData[])
            setLoading(false)
          },
          error: (error: Papa.ParseError) => {
            console.error('Error parsing CSV:', error)
            setLoading(false)
          }
        })
      } catch (error) {
        console.error('Error fetching data:', error)
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Analytics calculations
  const totalCalls = data.length
  const successfulCalls = data.filter(call => call.status === 'completed').length
  const successRate = totalCalls > 0 ? ((successfulCalls / totalCalls) * 100).toFixed(1) : '0'
  
  const totalDuration = data.reduce((sum, call) => {
    const duration = parseInt(call.estimated_duration_seconds) || 0
    return sum + duration
  }, 0)
  
  const avgDuration = totalCalls > 0 ? Math.round(totalDuration / totalCalls) : 0

  // Intent distribution for pie chart
  const intentCounts = data.reduce((acc, call) => {
    const intent = call.intent || 'OTHER'
    acc[intent] = (acc[intent] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const pieData = {
    labels: Object.keys(intentCounts),
    datasets: [{
      data: Object.values(intentCounts),
      backgroundColor: [
        '#dc3545', '#007bff', '#28a745', '#ffc107', 
        '#17a2b8', '#6f42c1', '#fd7e14', '#6c757d'
      ]
    }]
  }

  // Daily trends for line chart
  const dailyCounts = data.reduce((acc, call) => {
    const date = call.call_date
    acc[date] = (acc[date] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const sortedDates = Object.keys(dailyCounts).sort()
  const lineData = {
    labels: sortedDates,
    datasets: [{
      label: 'Calls per Day',
      data: sortedDates.map(date => dailyCounts[date]),
      borderColor: '#1e40af',
      backgroundColor: 'rgba(30, 64, 175, 0.1)',
      tension: 0.1
    }]
  }

  // Agent performance for bar chart
  const agentCounts = data.reduce((acc, call) => {
    const agent = call.agent_name || 'Unknown'
    acc[agent] = (acc[agent] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const barData = {
    labels: Object.keys(agentCounts),
    datasets: [{
      label: 'Calls Handled',
      data: Object.values(agentCounts),
      backgroundColor: '#3b82f6'
    }]
  }

  // Filter data
  const filteredData = data.filter(call => {
    const matchesSearch = call.transcription?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         call.summary?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         call.agent_name?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesIntent = selectedIntent === 'all' || call.intent === selectedIntent
    return matchesSearch && matchesIntent
  })

  const getIntentBadgeClass = (intent: string) => {
    const intentClass = intent?.toLowerCase().replace('_', '') || 'other'
    return `badge badge-${intentClass}`
  }

  const formatDuration = (seconds: string) => {
    const secs = parseInt(seconds) || 0
    const mins = Math.floor(secs / 60)
    const remainingSecs = secs % 60
    return `${mins}:${remainingSecs.toString().padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div className="container-fluid py-4">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2">Loading call analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container-fluid py-4">
      {/* Key Metrics */}
      <div className="row mb-4">
        <div className="col-lg-3 col-md-6 mb-3">
          <div className="metric-card metric-card-primary">
            <div className="d-flex align-items-center">
              <i className="bi bi-telephone-fill fs-1 me-3"></i>
              <div>
                <div className="metric-value">{totalCalls}</div>
                <div className="metric-label">Total Calls</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-lg-3 col-md-6 mb-3">
          <div className="metric-card metric-card-success">
            <div className="d-flex align-items-center">
              <i className="bi bi-check-circle-fill fs-1 me-3"></i>
              <div>
                <div className="metric-value">{successRate}%</div>
                <div className="metric-label">Success Rate</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-lg-3 col-md-6 mb-3">
          <div className="metric-card metric-card-warning">
            <div className="d-flex align-items-center">
              <i className="bi bi-clock-fill fs-1 me-3"></i>
              <div>
                <div className="metric-value">{formatDuration(avgDuration.toString())}</div>
                <div className="metric-label">Avg Duration</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-lg-3 col-md-6 mb-3">
          <div className="metric-card metric-card-info">
            <div className="d-flex align-items-center">
              <i className="bi bi-graph-up fs-1 me-3"></i>
              <div>
                <div className="metric-value">{Object.keys(intentCounts).length}</div>
                <div className="metric-label">Intent Types</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="row mb-4">
        <div className="col-lg-4 mb-3">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="card-title mb-0">Intent Distribution</h5>
            </div>
            <div className="card-body">
              <div className="chart-container">
                <Pie data={pieData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-lg-4 mb-3">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="card-title mb-0">Daily Trends</h5>
            </div>
            <div className="card-body">
              <div className="chart-container">
                <Line data={lineData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-lg-4 mb-3">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="card-title mb-0">Agent Performance</h5>
            </div>
            <div className="card-body">
              <div className="chart-container">
                <Bar data={barData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="row">
        <div className="col-12">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="card-title mb-0">Call Transcriptions</h5>
              <div className="d-flex gap-2">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search transcriptions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{ width: '300px' }}
                />
                <select
                  className="form-select"
                  value={selectedIntent}
                  onChange={(e) => setSelectedIntent(e.target.value)}
                  style={{ width: 'auto' }}
                >
                  <option value="all">All Intents</option>
                  {Object.keys(intentCounts).map(intent => (
                    <option key={intent} value={intent}>{intent}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Date/Time</th>
                      <th>Agent</th>
                      <th>Duration</th>
                      <th>Intent</th>
                      <th>Summary</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredData.map((call, index) => (
                      <tr key={index}>
                        <td>
                          <div>{call.call_date}</div>
                          <small className="text-muted">{call.call_time}</small>
                        </td>
                        <td>{call.agent_name || 'Unknown'}</td>
                        <td>{formatDuration(call.estimated_duration_seconds)}</td>
                        <td>
                          <span className={`badge ${getIntentBadgeClass(call.intent)}`}>
                            {call.intent || 'OTHER'}
                          </span>
                        </td>
                        <td>
                          <div style={{ maxWidth: '300px' }}>
                            {call.summary || 'No summary available'}
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${call.status === 'completed' ? 'bg-success' : 'bg-warning'}`}>
                            {call.status || 'Unknown'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="card-footer text-muted">
              Showing {filteredData.length} of {totalCalls} calls
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}