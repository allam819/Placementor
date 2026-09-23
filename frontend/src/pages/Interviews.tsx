import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useNavigate, useLocation } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Code2, MessagesSquare, Briefcase, FileText, Bot, User, CheckCircle2, AlertCircle, Target } from 'lucide-react'
import { cn } from '../lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function Interviews() {
  const [resumes, setResumes] = useState<any[]>([])
  const [selectedResumeId, setSelectedResumeId] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [difficulty, setDifficulty] = useState('intermediate')
  const [mode, setMode] = useState('dsa')
  const [recommendation, setRecommendation] = useState<any>(null)
  const [fetchingRec, setFetchingRec] = useState(false)
  const [useRecommendation, setUseRecommendation] = useState(true)
  
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
      navigate(location.pathname, { replace: true, state: {} })
    }
    fetchResumes()
  }, [location, navigate])

  const fetchResumes = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    const { data } = await supabase.from('resumes').select('*').order('created_at', { ascending: false })
    if (data) {
      setResumes(data)
      if (data.length > 0) setSelectedResumeId(data[0].id)
    }
  }
  
  const fetchRecommendation = async () => {
    setFetchingRec(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    try {
      const res = await fetch('http://127.0.0.1:8000/api/interviews/recommend-dsa', {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (res.ok) {
        setRecommendation(await res.json())
      }
    } catch (e) {}
    setFetchingRec(false)
  }

  useEffect(() => {
    if (mode === 'dsa' && !recommendation && !fetchingRec) {
      fetchRecommendation()
    }
  }, [mode])

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
        body: JSON.stringify({ 
          resume_id: selectedResumeId, 
          target_role: targetRole, 
          difficulty, 
          mode,
          problem_id: (mode === 'dsa' && useRecommendation && recommendation) ? recommendation.problem.id : undefined,
          selection_mode: (mode === 'dsa' && useRecommendation && recommendation) ? 'adaptive' : 'manual'
        })
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
    } catch (err) {}
    setLoading(false)
  }

  const handleEnd = async () => {
    if (!confirm("Are you sure you want to end this interview?")) return
    setLoading(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/interviews/${sessionId}/evaluate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (res.ok) {
        setEvaluation(await res.json())
        setSessionId(null)
      } else {
        alert("Failed to evaluate: " + await res.text())
      }
    } catch (err) {}
    setLoading(false)
  }

  if (evaluation) {
    return (
      <div className="max-w-4xl mx-auto space-y-8 pb-10 animate-in">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Performance Review</h2>
            <p className="text-gray-500 mt-1">Detailed feedback from your recent mock interview.</p>
          </div>
          <Button onClick={() => setEvaluation(null)}>Start Another Interview</Button>
        </div>
        
        <Card className="border-blue-100 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-8 text-white flex justify-between items-center">
             <div>
               <h3 className="text-2xl font-bold">Overall Score</h3>
               <p className="text-blue-100 mt-1">Based on technical accuracy and communication.</p>
             </div>
             <div className="text-5xl font-black">{evaluation.overall_score}<span className="text-2xl opacity-70">/100</span></div>
          </div>
          <CardContent className="p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" /> Strengths
                </h4>
                <ul className="space-y-2">
                  {evaluation.strengths?.map((s: string, i: number) => (
                    <li key={i} className="text-sm text-gray-700 bg-emerald-50/50 p-2.5 rounded border border-emerald-100 flex items-start gap-2">
                      <span className="text-emerald-500 mt-0.5">•</span> {s}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                  <AlertCircle className="h-5 w-5 text-red-500" /> Weaknesses & Gaps
                </h4>
                <div className="space-y-3">
                  {evaluation.weaknesses?.map((w: any, i: number) => (
                    <div key={i} className="text-sm text-gray-700 bg-red-50/50 p-3 rounded border border-red-100">
                      <div className="font-semibold text-gray-900 mb-1">{w.topic}</div>
                      <div className="text-gray-600 mb-2">{w.issue}</div>
                      {w.learning_recommendations?.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-red-100/50">
                          <span className="text-xs font-semibold text-red-800 uppercase">Recommended:</span>
                          <span className="text-xs ml-2 text-gray-600">{w.learning_recommendations.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (sessionId) {
    return (
      <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col animate-in">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Live Interview</h2>
            <p className="text-sm text-gray-500">General Technical & Behavioral</p>
          </div>
          <Button variant="destructive" onClick={handleEnd} isLoading={loading}>
            End & Evaluate
          </Button>
        </div>
        
        <Card className="flex-1 flex flex-col overflow-hidden bg-gray-50 border-gray-200">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg, i) => {
              const content = msg.content ? msg.content.replace(/\\n/g, '\n').replace(/\\"/g, '"') : ''
              const isUser = msg.role === 'user'
              return (
                <div key={i} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                  <div className={cn(
                    "max-w-[80%] rounded-2xl p-4 shadow-sm",
                    isUser ? "bg-blue-600 text-white rounded-br-none" : "bg-white border border-gray-200 text-gray-900 rounded-bl-none"
                  )}>
                    {!isUser && (
                      <div className="flex items-center gap-2 mb-2">
                        <div className="h-6 w-6 rounded-full bg-blue-100 flex items-center justify-center">
                          <Bot className="h-3 w-3 text-blue-700" />
                        </div>
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Interviewer</span>
                      </div>
                    )}
                    <div className={cn("prose prose-sm max-w-none", isUser ? "prose-invert" : "")}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              )
            })}
            {loading && messages[messages.length-1]?.role === 'user' && (
              <div className="flex justify-start">
                 <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-none p-4 shadow-sm flex items-center gap-3 text-gray-500">
                   <div className="flex gap-1">
                     <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                     <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                     <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                   </div>
                   <span className="text-sm italic">Thinking...</span>
                 </div>
              </div>
            )}
          </div>
          
          <div className="p-4 bg-white border-t border-gray-200">
            <form onSubmit={handleSend} className="flex gap-3">
              <input
                type="text"
                value={currentInput}
                onChange={e => setCurrentInput(e.target.value)}
                placeholder="Type your response..."
                className="flex-1 rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                disabled={loading}
                autoFocus
              />
              <Button type="submit" disabled={!currentInput.trim() || loading} className="px-6 h-auto py-3">
                Send
              </Button>
            </form>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto pb-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">Start an Interview</h1>
        <p className="text-gray-500">Practice with our stateful AI interviewer tailored to your exact profile.</p>
      </div>
      
      <form onSubmit={handleStart}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card 
            className={cn("cursor-pointer transition-all hover:border-blue-300 hover:shadow-md", mode === 'dsa' ? "border-blue-600 ring-1 ring-blue-600 bg-blue-50/10" : "")}
            onClick={() => setMode('dsa')}
          >
            <CardContent className="p-6">
              <div className="h-10 w-10 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center mb-4">
                <Code2 className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">DSA Technical Round</h3>
              <p className="text-sm text-gray-500">Live coding environment with an agentic interviewer simulating a FAANG process.</p>
            </CardContent>
          </Card>
          
          <Card 
            className={cn("cursor-pointer transition-all hover:border-blue-300 hover:shadow-md", mode === 'general' ? "border-blue-600 ring-1 ring-blue-600 bg-blue-50/10" : "")}
            onClick={() => setMode('general')}
          >
            <CardContent className="p-6">
              <div className="h-10 w-10 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center mb-4">
                <MessagesSquare className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">General / Behavioral</h3>
              <p className="text-sm text-gray-500">Conversational deep-dive into your resume experience and core competencies.</p>
            </CardContent>
          </Card>
        </div>
        
        <Card>
          <CardHeader className="border-b border-gray-100 bg-gray-50/50">
            <CardTitle className="text-lg">Interview Configuration</CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-gray-400" /> Active Resume
                </label>
                <select 
                  value={selectedResumeId} 
                  onChange={e => setSelectedResumeId(e.target.value)} 
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  required
                >
                  <option value="" disabled>-- Select resume --</option>
                  {resumes.map(r => <option key={r.id} value={r.id}>{r.file_name}</option>)}
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-gray-400" /> Target Role
                </label>
                <input 
                  type="text" 
                  value={targetRole} 
                  onChange={e => setTargetRole(e.target.value)} 
                  placeholder="e.g. Frontend Engineer" 
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" 
                  required 
                />
              </div>
            </div>
            
            {mode === 'dsa' && (
              <div className="space-y-6 pt-4 border-t border-gray-100">
                {fetchingRec ? (
                  <div className="flex items-center justify-center p-8 bg-gray-50 rounded-lg border border-gray-100 border-dashed">
                    <span className="text-sm text-gray-500 animate-pulse flex items-center gap-2">
                      <Target className="h-4 w-4 animate-spin" /> Analyzing preparation profile...
                    </span>
                  </div>
                ) : recommendation ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        <Target className="h-4 w-4 text-blue-500" /> Recommended for You
                      </label>
                      <button 
                        type="button" 
                        onClick={() => setUseRecommendation(!useRecommendation)}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {useRecommendation ? 'Choose manually instead' : 'Use recommendation'}
                      </button>
                    </div>
                    
                    {useRecommendation ? (
                      <div className="bg-blue-50/50 border border-blue-100 rounded-lg p-5 transition-all">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold text-gray-900">{recommendation.problem.title}</h4>
                            <div className="flex gap-2 mt-1.5">
                              <span className={cn("text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full", recommendation.problem.difficulty.toLowerCase() === 'easy' ? "bg-emerald-100 text-emerald-700" : recommendation.problem.difficulty.toLowerCase() === 'medium' ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700")}>
                                {recommendation.problem.difficulty}
                              </span>
                            </div>
                          </div>
                          <div className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded">Score: {recommendation.score}</div>
                        </div>
                        
                        <div className="mt-4 space-y-1.5">
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Why this problem?</p>
                          <ul className="space-y-1">
                            {recommendation.reasons.map((reason: string, i: number) => (
                              <li key={i} className="text-sm text-gray-700 flex items-start gap-1.5">
                                <span className="text-blue-400 mt-0.5">•</span> {reason}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                        <label className="text-sm font-medium text-gray-700">Select Difficulty Level</label>
                        <div className="flex gap-3">
                          {['beginner', 'intermediate', 'advanced'].map(level => (
                            <button
                              key={level}
                              type="button"
                              onClick={() => setDifficulty(level)}
                              className={cn(
                                "flex-1 py-2 px-4 rounded-md border text-sm font-medium capitalize transition-colors",
                                difficulty === level 
                                  ? "bg-blue-600 text-white border-blue-600" 
                                  : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                              )}
                            >
                              {level}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                      <Target className="h-4 w-4 text-gray-400" /> Difficulty Level
                    </label>
                    <div className="flex gap-3">
                      {['beginner', 'intermediate', 'advanced'].map(level => (
                        <button
                          key={level}
                          type="button"
                          onClick={() => setDifficulty(level)}
                          className={cn(
                            "flex-1 py-2 px-4 rounded-md border text-sm font-medium capitalize transition-colors",
                            difficulty === level 
                              ? "bg-blue-600 text-white border-blue-600" 
                              : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                          )}
                        >
                          {level}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            <div className="pt-6">
              <Button type="submit" size="lg" className="w-full text-base" isLoading={loading}>
                Launch Interview Environment
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}
