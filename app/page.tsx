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
  call_datetime: string
  phone_number: string
  call_status: string
  agent_name: string
  estimated_duration_seconds: string
  file_size: string
  duration: string
  transcription: string
  summary: string
  intent: string
  status: string
  processing_time: string
  error_message: string
  sub_intent: string
  diarized_transcription: string
  speaker_count: string
  primary_disposition: string
  secondary_disposition: string
}

export default function Dashboard() {
  const [data, setData] = useState<CallData[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedIntent, setSelectedIntent] = useState('all')
  const [selectedSubIntent, setSelectedSubIntent] = useState('all')
  const [selectedPrimaryDisposition, setSelectedPrimaryDisposition] = useState('all')
  const [selectedSecondaryDisposition, setSelectedSecondaryDisposition] = useState('all')
  const [selectedAgent, setSelectedAgent] = useState('all')
  const [selectedCallStatus, setSelectedCallStatus] = useState('all')
  const [showTranscriptionModal, setShowTranscriptionModal] = useState(false)
  const [selectedCallForTranscription, setSelectedCallForTranscription] = useState<CallData | null>(null)

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

  // Get unique values for filters
  const uniqueIntents = [...new Set(data.map(call => call.intent).filter(Boolean))].sort()
  const uniqueSubIntents = [...new Set(data.map(call => call.sub_intent).filter(Boolean))].sort()
  const uniquePrimaryDispositions = [...new Set(data.map(call => call.primary_disposition).filter(Boolean))].sort()
  const uniqueSecondaryDispositions = [...new Set(data.map(call => call.secondary_disposition).filter(Boolean))].sort()
  const uniqueAgents = [...new Set(data.map(call => call.agent_name).filter(Boolean))].sort()
  const uniqueCallStatuses = [...new Set(data.map(call => call.call_status).filter(Boolean))].sort()

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

  // Sub-intent distribution
  const subIntentCounts = data.reduce((acc, call) => {
    const subIntent = call.sub_intent || 'UNKNOWN'
    acc[subIntent] = (acc[subIntent] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const subIntentData = {
    labels: Object.keys(subIntentCounts),
    datasets: [{
      data: Object.values(subIntentCounts),
      backgroundColor: [
        '#ff6384', '#36a2eb', '#cc65fe', '#ffce56', 
        '#4bc0c0', '#ff9f40', '#ff6384', '#c9cbcf'
      ]
    }]
  }

  // Primary disposition distribution
  const primaryDispositionCounts = data.reduce((acc, call) => {
    const disposition = call.primary_disposition || 'UNKNOWN'
    acc[disposition] = (acc[disposition] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const dispositionData = {
    labels: Object.keys(primaryDispositionCounts),
    datasets: [{
      data: Object.values(primaryDispositionCounts),
      backgroundColor: [
        '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', 
        '#06b6d4', '#f97316', '#ec4899', '#6b7280'
      ]
    }]
  }

  // Call status distribution
  const callStatusCounts = data.reduce((acc, call) => {
    const status = call.call_status || 'Unknown'
    acc[status] = (acc[status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const callStatusData = {
    labels: Object.keys(callStatusCounts),
    datasets: [{
      label: 'Call Status',
      data: Object.values(callStatusCounts),
      backgroundColor: '#17a2b8'
    }]
  }

  // Filter data
  const filteredData = data.filter(call => {
    const matchesSearch = call.transcription?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         call.summary?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         call.agent_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         call.filename?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesIntent = selectedIntent === 'all' || call.intent === selectedIntent
    const matchesSubIntent = selectedSubIntent === 'all' || call.sub_intent === selectedSubIntent
    const matchesPrimaryDisposition = selectedPrimaryDisposition === 'all' || call.primary_disposition === selectedPrimaryDisposition
    const matchesSecondaryDisposition = selectedSecondaryDisposition === 'all' || call.secondary_disposition === selectedSecondaryDisposition
    const matchesAgent = selectedAgent === 'all' || call.agent_name === selectedAgent
    const matchesCallStatus = selectedCallStatus === 'all' || call.call_status === selectedCallStatus
    
    return matchesSearch && matchesIntent && matchesSubIntent && matchesPrimaryDisposition && 
           matchesSecondaryDisposition && matchesAgent && matchesCallStatus
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

  const openTranscriptionModal = (call: CallData) => {
    setSelectedCallForTranscription(call)
    setShowTranscriptionModal(true)
  }

  const closeTranscriptionModal = () => {
    setShowTranscriptionModal(false)
    setSelectedCallForTranscription(null)
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

      {/* Charts Row 1 */}
      <div className="row mb-4">
        <div className="col-lg-3 mb-3">
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
        
        <div className="col-lg-3 mb-3">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="card-title mb-0">Sub-Intent Distribution</h5>
            </div>
            <div className="card-body">
              <div className="chart-container">
                <Pie data={subIntentData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-lg-3 mb-3">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="card-title mb-0">Primary Disposition</h5>
            </div>
            <div className="card-body">
              <div className="chart-container">
                <Pie data={dispositionData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-lg-3 mb-3">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="card-title mb-0">Call Status</h5>
            </div>
            <div className="card-body">
              <div className="chart-container">
                <Bar data={callStatusData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="row mb-4">
        <div className="col-lg-6 mb-3">
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
        
        <div className="col-lg-6 mb-3">
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

      {/* Filters Row */}
      <div className="row mb-4">
        <div className="col-12">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">Filters & Search</h5>
            </div>
            <div className="card-body">
              <div className="row g-3">
                <div className="col-lg-3">
                  <label className="form-label">Search</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Search transcriptions, summary, agent..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="col-lg-2">
                  <label className="form-label">Intent</label>
                  <select
                    className="form-select"
                    value={selectedIntent}
                    onChange={(e) => setSelectedIntent(e.target.value)}
                  >
                    <option value="all">All Intents</option>
                    {uniqueIntents.map(intent => (
                      <option key={intent} value={intent}>{intent}</option>
                    ))}
                  </select>
                </div>
                <div className="col-lg-2">
                  <label className="form-label">Sub-Intent</label>
                  <select
                    className="form-select"
                    value={selectedSubIntent}
                    onChange={(e) => setSelectedSubIntent(e.target.value)}
                  >
                    <option value="all">All Sub-Intents</option>
                    {uniqueSubIntents.map(subIntent => (
                      <option key={subIntent} value={subIntent}>{subIntent}</option>
                    ))}
                  </select>
                </div>
                <div className="col-lg-2">
                  <label className="form-label">Agent</label>
                  <select
                    className="form-select"
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                  >
                    <option value="all">All Agents</option>
                    {uniqueAgents.map(agent => (
                      <option key={agent} value={agent}>{agent}</option>
                    ))}
                  </select>
                </div>
                <div className="col-lg-3">
                  <label className="form-label">Primary Disposition</label>
                  <select
                    className="form-select"
                    value={selectedPrimaryDisposition}
                    onChange={(e) => setSelectedPrimaryDisposition(e.target.value)}
                  >
                    <option value="all">All Primary Dispositions</option>
                    {uniquePrimaryDispositions.map(disposition => (
                      <option key={disposition} value={disposition}>{disposition}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="row g-3 mt-2">
                <div className="col-lg-3">
                  <label className="form-label">Secondary Disposition</label>
                  <select
                    className="form-select"
                    value={selectedSecondaryDisposition}
                    onChange={(e) => setSelectedSecondaryDisposition(e.target.value)}
                  >
                    <option value="all">All Secondary Dispositions</option>
                    {uniqueSecondaryDispositions.map(disposition => (
                      <option key={disposition} value={disposition}>{disposition}</option>
                    ))}
                  </select>
                </div>
                <div className="col-lg-2">
                  <label className="form-label">Call Status</label>
                  <select
                    className="form-select"
                    value={selectedCallStatus}
                    onChange={(e) => setSelectedCallStatus(e.target.value)}
                  >
                    <option value="all">All Call Status</option>
                    {uniqueCallStatuses.map(status => (
                      <option key={status} value={status}>{status}</option>
                    ))}
                  </select>
                </div>
                <div className="col-lg-2">
                  <label className="form-label">Actions</label>
                  <div>
                    <button 
                      className="btn btn-outline-secondary me-2"
                      onClick={() => {
                        setSearchTerm('')
                        setSelectedIntent('all')
                        setSelectedSubIntent('all')
                        setSelectedPrimaryDisposition('all')
                        setSelectedSecondaryDisposition('all')
                        setSelectedAgent('all')
                        setSelectedCallStatus('all')
                      }}
                    >
                      Clear All
                    </button>
                  </div>
                </div>
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
              <div className="text-muted">
                Showing {filteredData.length} of {totalCalls} calls
              </div>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Date/Time</th>
                      <th>Agent</th>
                      <th>Phone</th>
                      <th>Duration</th>
                      <th>Call Status</th>
                      <th>Intent</th>
                      <th>Sub-Intent</th>
                      <th>Primary Disp.</th>
                      <th>Secondary Disp.</th>
                      <th>Summary</th>
                      <th>Transcription</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredData.map((call, index) => (
                      <tr key={index}>
                        <td>
                          <div className="fw-bold">{call.call_date}</div>
                          <small className="text-muted">{call.call_time}</small>
                        </td>
                        <td>
                          <div className="fw-bold">{call.agent_name || 'Unknown'}</div>
                          <small className="text-muted">{call.filename}</small>
                        </td>
                        <td>{call.phone_number}</td>
                        <td>{formatDuration(call.estimated_duration_seconds)}</td>
                        <td>
                          <span className={`badge ${
                            call.call_status === 'answered' ? 'bg-success' : 
                            call.call_status === 'HangUp' ? 'bg-warning' : 'bg-secondary'
                          }`}>
                            {call.call_status}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${getIntentBadgeClass(call.intent)}`}>
                            {call.intent || 'OTHER'}
                          </span>
                        </td>
                        <td>
                          <span className="badge bg-info">
                            {call.sub_intent || 'N/A'}
                          </span>
                        </td>
                        <td>
                          <span className="badge bg-success">
                            {call.primary_disposition || 'N/A'}
                          </span>
                        </td>
                        <td>
                          <span className="badge bg-warning text-dark">
                            {call.secondary_disposition || 'N/A'}
                          </span>
                        </td>
                        <td>
                          <div style={{ maxWidth: '200px', fontSize: '0.9rem' }}>
                            {call.summary || 'No summary available'}
                          </div>
                        </td>
                        <td>
                          <button
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => openTranscriptionModal(call)}
                          >
                            <i className="bi bi-file-text me-1"></i>
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Transcription Modal */}
      {showTranscriptionModal && selectedCallForTranscription && (
        <div className="modal fade show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg modal-dialog-scrollable">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  Call Transcription - {selectedCallForTranscription.filename}
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={closeTranscriptionModal}
                ></button>
              </div>
              <div className="modal-body">
                <div className="row mb-3">
                  <div className="col-md-6">
                    <strong>Date:</strong> {selectedCallForTranscription.call_date}<br/>
                    <strong>Time:</strong> {selectedCallForTranscription.call_time}<br/>
                    <strong>Agent:</strong> {selectedCallForTranscription.agent_name}<br/>
                    <strong>Phone:</strong> {selectedCallForTranscription.phone_number}
                  </div>
                  <div className="col-md-6">
                    <strong>Duration:</strong> {formatDuration(selectedCallForTranscription.estimated_duration_seconds)}<br/>
                    <strong>Intent:</strong> <span className={`badge ${getIntentBadgeClass(selectedCallForTranscription.intent)}`}>{selectedCallForTranscription.intent}</span><br/>
                    <strong>Sub-Intent:</strong> <span className="badge bg-info">{selectedCallForTranscription.sub_intent}</span><br/>
                    <strong>Speakers:</strong> {selectedCallForTranscription.speaker_count}
                  </div>
                </div>
                
                <div className="mb-3">
                  <h6>Summary:</h6>
                  <p className="border rounded p-3 bg-light">
                    {selectedCallForTranscription.summary || 'No summary available'}
                  </p>
                </div>

                <div className="mb-3">
                  <h6>Full Transcription:</h6>
                  <div className="border rounded p-3" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    <p style={{ whiteSpace: 'pre-wrap' }}>
                      {selectedCallForTranscription.transcription || 'No transcription available'}
                    </p>
                  </div>
                </div>

                {selectedCallForTranscription.diarized_transcription && (
                  <div className="mb-3">
                    <h6>Diarized Transcription (Speaker Separated):</h6>
                    <div className="border rounded p-3" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                      <p style={{ whiteSpace: 'pre-wrap' }}>
                        {selectedCallForTranscription.diarized_transcription}
                      </p>
                    </div>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={closeTranscriptionModal}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}