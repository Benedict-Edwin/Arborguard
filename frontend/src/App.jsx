import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Upload, AlertTriangle, CheckCircle, Clock, ShieldAlert, FileVideo, Download } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE = '/api'

function App() {
  const [file, setFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResults(null)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const res = await axios.post(`${API_BASE}/upload`, formData)
      setJobId(res.data.job_id)
      setStatus('processing')
    } catch (err) {
      setError("Upload failed. Ensure backend is running.")
      setLoading(false)
    }
  }

  // Poll status
  useEffect(() => {
    let interval
    if (jobId && status === 'processing') {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_BASE}/status/${jobId}`)
          if (res.data.status === 'completed') {
            setResults(res.data)
            setStatus('completed')
            setLoading(false)
            clearInterval(interval)
          } else if (res.data.status === 'failed') {
            setError(res.data.error)
            setStatus('failed')
            setLoading(false)
            clearInterval(interval)
          }
        } catch (err) {
          console.error("Polling error", err)
        }
      }, 2000)
    }
    return () => clearInterval(interval)
  }, [jobId, status])

  const highRiskAnomalies = results?.logs?.flatMap(l => 
    l.anomalies.filter(a => a.risk === 'HIGH').map(a => ({...a, timestamp: l.timestamp}))
  ) || []

  return (
    <div className="dashboard">
      <header>
        <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
          <ShieldAlert size={48} color="#60a5fa" style={{ marginBottom: '1rem' }} />
          <h1>ArborGuard AI</h1>
          <p>Automated Tree & Powerline Enomaly Detection</p>
        </motion.div>
      </header>

      <main>
        {/* Upload Section */}
        <section className="upload-section">
          {!jobId || status === 'completed' || status === 'failed' ? (
            <motion.div whileHover={{ scale: 1.02 }} className="upload-container">
              <Upload size={48} color="#94a3b8" style={{ marginBottom: '1rem' }} />
              <h3>{file ? file.name : "Drag and drop your footage (MP4)"}</h3>
              <input 
                type="file" 
                accept="video/mp4" 
                onChange={handleFileChange} 
                style={{ display: 'none' }} 
                id="file-input"
              />
              <label htmlFor="file-input" className="btn-upload" style={{ display: 'inline-block' }}>
                Select Video
              </label>
              {file && (
                <button onClick={handleUpload} disabled={loading} className="btn-upload" style={{ marginLeft: '1rem', background: '#34d399' }}>
                  {loading ? "Processing..." : "Start Analysis"}
                </button>
              )}
            </motion.div>
          ) : (
            <div className="processing-container">
              <Clock size={48} className="spin" color="#60a5fa" style={{ marginBottom: '1rem' }} />
              <h3>AI Engine analyzing footage...</h3>
              <div className="progress-container">
                <div className="progress-bar" style={{ width: '60%' }}></div>
              </div>
              <p>Extracting frames and detecting risky proximities.</p>
            </div>
          )}
          {error && <p style={{ color: '#f87171', marginTop: '1rem' }}><AlertTriangle size={16} /> {error}</p>}
        </section>

        {/* Results Section */}
        <AnimatePresence>
          {results && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{results.high_risk_count}</div>
                  <div className="stat-label">Critical Risks</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{(results.logs.length / 1).toFixed(1)}s</div>
                  <div className="stat-label">Time Coverage</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">AI-CNN</div>
                  <div className="stat-label">Model Engine</div>
                </div>
              </div>

              <div className="results-section">
                {/* Video Player */}
                <div className="video-container">
                  <h4 style={{ padding: '1rem', background: '#1e293b', margin: 0 }}>Annotated Feedback</h4>
                  <video controls src={`${API_BASE}${results.output_video}`} />
                  <div style={{ padding: '1rem', textAlign: 'right' }}>
                    <a href={`${API_BASE}${results.output_video}`} download className="btn-upload" style={{ textDecoration: 'none', background: '#475569' }}>
                      <Download size={16} /> Download Report
                    </a>
                  </div>
                </div>

                {/* High Risk Moments */}
                <div className="snapshots-list">
                  <h4 style={{ marginBottom: '1rem' }}>Critical Snapshots</h4>
                  <div className="snapshots-grid">
                    {highRiskAnomalies.length > 0 ? (
                      highRiskAnomalies.map((anno, idx) => (
                        <motion.div key={idx} whileHover={{ x: 5 }} className="snapshot-card">
                           {/* Placeholder Snapshot logic: use generic path if specific one missing */}
                          <div className="snapshot-info">
                            <span className="risk-tag risk-high">HIGH RISK</span>
                            <p style={{ margin: 0, fontSize: '0.8rem' }}>Frame Log {idx}</p>
                            <p style={{ margin: 0, fontSize: '0.7rem', color: '#64748b' }}>Detection: Tree encroachment detected @ {idx}</p>
                          </div>
                        </motion.div>
                      ))
                    ) : (
                      <p>No high-risk anomalies detected.</p>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <style>{`
        .spin { animation: spin 2s linear infinite; }
        @keyframes spin { from {transform: rotate(0deg);} to {transform: rotate(360deg);} }
      `}</style>
    </div>
  )
}

export default App
