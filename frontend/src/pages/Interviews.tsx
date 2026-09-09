import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useNavigate, useLocation } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function Interviews() {
  const [resumes, setResumes] = useState<any[]>([])
  const [selectedResumeId, setSelectedResumeId] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [difficulty, setDifficulty] = useState('intermediate')
  const [mode, setMode] = useState('general')
  
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<{role: string, content: string}[]>([])
  const [currentInput, setCurrentInput] = useState('')
  const [loading, setLoading] = useState(false)
  
  const [evaluation, setEvaluation] = useState<any>(null)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    if (location.state?.evaluation) {
      setEvaluation(location.state.evaluation)
      // clear the state properly via react router
      navigate(location.pathname, { replace: true, state: {} })
    }
    fetchResumes()
  }, [location, navigate])

  const fetchResumes = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    const { data } = await supabase.from('resumes').select('*').order('created_at', { ascending: false })
    if (data) setResumes(data)
  }

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedResumeId || !targetRole) return alert('Please select a resume and target role.')
    
    setLoading(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/interviews/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ resume_id: selectedResumeId, target_role: targetRole, difficulty, mode })
      })
      if (res.ok) {
        const data = await res.json()
        if (mode === 'dsa') {
          navigate(`/interview/dsa/${data.session_id}`)
        } else {
          setSessionId(data.session_id)
          setMessages([{ role: 'assistant', content: data.message }])
        }
      } else {
        alert('Failed to start: ' + await res.text())
      }
    } catch (err) {
      alert('Error starting interview')
    }
    setLoading(false)
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentInput.trim() || !sessionId) return
    
    const userMsg = currentInput
    setCurrentInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    
    setLoading(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/interviews/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ session_id: sessionId, content: userMsg })
      })
      if (res.ok) {
        const data = await res.json()
        setMessages(prev => [...prev, { role: 'assistant', content: data.message }])
      } else {
        alert('Failed to send: ' + await res.text())
      }
    } catch (err) {
      alert('Error sending message')
    }
    setLoading(false)
  }

  const handleEnd = async () => {
    if (!sessionId) return
    setLoading(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/interviews/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ session_id: sessionId })
      })
      if (res.ok) {
        const data = await res.json()
        setEvaluation(data)
      } else {
        alert('Failed to evaluate: ' + await res.text())
      }
    } catch (err) {
      alert('Error ending interview')
    }
    setLoading(false)
  }

  if (evaluation) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <h2 className="text-2xl font-bold text-center mb-8">Interview Results</h2>
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center">
          <div className="text-6xl font-bold text-blue-600 mb-4">{evaluation.overall_score}/100</div>
          <p className="text-gray-600 mb-8">Overall Performance Score</p>
          
          <div className="space-y-6 text-left">
            {evaluation.categories.map((cat: any, i: number) => (
              <div key={i} className="border-b pb-4 last:border-0">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-semibold text-lg">{cat.category}</h4>
                  <span className="bg-gray-100 text-gray-800 text-xs font-medium px-2.5 py-0.5 rounded">{cat.score}/10</span>
                </div>
                <p className="text-gray-600 text-sm">{cat.feedback}</p>
              </div>
            ))}
          </div>
          
          <button onClick={() => {setEvaluation(null); setSessionId(null); setMessages([])}} className="mt-8 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700">
            Start New Interview
          </button>
        </div>
      </div>
    )
  }

  if (sessionId) {
    return (
      <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Live Interview</h2>
          <button onClick={handleEnd} disabled={loading} className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50">
            {loading ? 'Evaluating...' : 'End & Evaluate'}
          </button>
        </div>
        
        <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 p-4 overflow-y-auto mb-4 space-y-4">
          {messages.map((msg, i) => {
            const content = msg.content ? msg.content.replace(/\\n/g, '\n').replace(/\\"/g, '"') : ''
            return (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[75%] rounded-lg p-4 shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-50 border border-gray-200 text-gray-800'}`}>
                  {msg.role === 'assistant' && <div className="text-xs text-gray-500 mb-2 font-bold uppercase tracking-wider">AI Interviewer</div>}
                  <div className={`prose prose-sm max-w-none ${msg.role === 'user' ? 'prose-invert' : ''}`}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            )
          })}
          {loading && messages[messages.length-1]?.role === 'user' && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-500 rounded-lg p-3 text-sm italic">Interviewer is thinking...</div>
            </div>
          )}
        </div>
        
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={currentInput}
            onChange={e => setCurrentInput(e.target.value)}
            placeholder="Type your answer here..."
            className="flex-1 rounded-md border border-gray-300 p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button type="submit" disabled={!currentInput.trim() || loading} className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 font-semibold">
            Send
          </button>
        </form>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto mt-10">
      <h2 className="text-2xl font-bold mb-4">Start AI Mock Interview</h2>
      <p className="text-gray-600 mb-8">Configure your interview simulation based on your parsed resume and target role.</p>
      
      <form onSubmit={handleStart} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Interview Mode</label>
          <select value={mode} onChange={e => setMode(e.target.value)} className="w-full rounded-md border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500">
            <option value="general">General / Behavioral Deep Dive</option>
            <option value="dsa">DSA Technical Round</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Resume</label>
          <select value={selectedResumeId} onChange={e => setSelectedResumeId(e.target.value)} className="w-full rounded-md border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500" required>
            <option value="">-- Choose a parsed resume --</option>
            {resumes.map(r => (
              <option key={r.id} value={r.id}>{r.file_name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Target Role</label>
          <input type="text" value={targetRole} onChange={e => setTargetRole(e.target.value)} placeholder="e.g. Frontend Developer, Data Scientist" className="w-full rounded-md border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500" required />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Difficulty</label>
          <select value={difficulty} onChange={e => setDifficulty(e.target.value)} className="w-full rounded-md border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500">
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
            <option value="expert">Expert (FAANG level)</option>
          </select>
        </div>
        
        <button type="submit" disabled={loading} className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 font-semibold text-lg">
          {loading ? 'Preparing Interviewer...' : 'Start Interview'}
        </button>
      </form>
    </div>
  )
}
