import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import Editor from '@monaco-editor/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function DSAInterviewWorkspace() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  
  const [language, setLanguage] = useState('python')
  const [problem, setProblem] = useState<any>(null)
  const [code, setCode] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loadingRun, setLoadingRun] = useState(false)
  
  const [messages, setMessages] = useState<any[]>([])
  const [chatInput, setChatInput] = useState('')
  const [loadingChat, setLoadingChat] = useState(true)

  useEffect(() => {
    fetchSessionData()
  }, [sessionId])

  const unescapeText = (text: string) => text ? text.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\"/g, '"') : ''

  const fetchSessionData = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return

    // 1. Fetch Session to get problem ID
    const sessionRes = await supabase.from('interview_sessions').select('*').eq('id', sessionId).single()
    if (sessionRes.data && sessionRes.data.dsa_problem_id) {
      // 2. Fetch Problem
      const res = await fetch(`http://127.0.0.1:8000/api/dsa/problems/${sessionRes.data.dsa_problem_id}`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (res.ok) {
        const data = await res.json()
        try {
          const parsed = JSON.parse(data.starter_code)
          data.starter_code = parsed
          setCode(unescapeText(parsed[language] || ''))
        } catch {
          setCode(unescapeText(data.starter_code || ''))
        }
        data.description = unescapeText(data.description)
        setProblem(data)
      }
    }

    // 3. Fetch Messages
    const msgRes = await supabase.from('interview_messages').select('role, content').eq('session_id', sessionId).order('created_at', { ascending: true })
    if (msgRes.data) {
      const msgs = msgRes.data.map(m => ({ ...m, content: unescapeText(m.content) }))
      setMessages(msgs)
    }
    setLoadingChat(false)
  }

  // Update code editor when language changes
  useEffect(() => {
    if (problem && problem.starter_code && typeof problem.starter_code === 'object') {
      setCode(problem.starter_code[language] || '')
    }
  }, [language])

  const runCode = async () => {
    setLoadingRun(true)
    setResult(null)
    
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return

    try {
      const res = await fetch('http://127.0.0.1:8000/api/dsa/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ problem_id: problem.id, code, language })
      })
      
      let executionFeedback = ""
      if (res.ok) {
        const out = await res.json()
        setResult(out)
        executionFeedback = out.status === 'Passed' ? 'Passed all tests!' : `Status: ${out.status}\\nFeedback: ${out.feedback}`
      } else {
        setResult({ status: 'Error', feedback: 'Failed to communicate with execution server.' })
        executionFeedback = 'Execution Server Error'
      }

      // Automatically notify AI that code was run
      sendChatMessage(null, executionFeedback)

    } catch (err) {
      setResult({ status: 'Error', feedback: 'Network error.' })
    }
    setLoadingRun(false)
  }
  
  const sendChatMessage = async (e: React.FormEvent | null, executionResults?: string) => {
    if (e) e.preventDefault()
    
    const userMsg = chatInput
    if (!userMsg.trim() && !executionResults) return
    
    if (userMsg.trim()) {
      setMessages(prev => [...prev, { role: 'user', content: userMsg }])
      setChatInput('')
    }
    
    setLoadingChat(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/interviews/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ 
          session_id: sessionId, 
          content: userMsg,
          current_code: code,
          execution_results: executionResults
        })
      })
      
      if (res.ok) {
        const data = await res.json()
        setMessages(prev => [...prev, { role: 'assistant', content: data.message }])
      } else {
        const errText = await res.text()
        alert('Failed to send message: ' + errText)
      }
    } catch (err: any) {
      alert('Error sending message: ' + err.message)
    }
    setLoadingChat(false)
  }

  const handleEnd = async () => {
    setLoadingChat(true)
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
        navigate('/interview', { state: { evaluation: data } })
      } else {
        alert('Failed to evaluate: ' + await res.text())
        setLoadingChat(false)
      }
    } catch (err: any) {
      alert('Error ending interview: ' + err.message)
      setLoadingChat(false)
    }
  }

  if (!problem) return <div className="p-8">Loading technical interview...</div>

  if (!problem) return <div className="p-8">Loading technical interview...</div>

  if (!problem) return <div className="p-8">Loading technical interview...</div>

  return (
    <div className="h-[calc(100vh-4rem)] flex -m-8 bg-white overflow-hidden">
      {/* Left Panel: Chat & Description */}
      <div className="w-[40%] flex flex-col border-r border-gray-200 bg-white overflow-hidden shrink-0">
        
        {/* Problem Description */}
        <div className="p-5 border-b border-gray-200 overflow-y-auto min-h-[30%] max-h-[40%] shrink-0">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-xl font-bold text-gray-900">{problem.title}</h2>
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-blue-100 text-blue-800 shrink-0">Technical Round</span>
          </div>
          <div className="prose prose-sm prose-gray max-w-none prose-pre:bg-gray-100 prose-pre:text-gray-900 prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1 prose-code:rounded break-words">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{problem.description}</ReactMarkdown>
          </div>
        </div>

        {/* Live Chat */}
        <div className="flex-1 overflow-hidden flex flex-col bg-gray-50">
          <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`p-4 rounded-xl max-w-[85%] text-sm shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'}`}>
                  {msg.role === 'assistant' && <div className="text-xs text-gray-500 mb-2 font-bold uppercase tracking-wider">AI Interviewer</div>}
                  <div className={`prose prose-sm max-w-none break-words ${msg.role === 'user' ? 'prose-invert' : ''}`}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
            {loadingChat && (
              <div className="text-sm text-gray-500 font-medium animate-pulse flex items-center gap-2">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <div className="p-4 bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] shrink-0">
            <form onSubmit={e => sendChatMessage(e)} className="flex gap-2 mb-3">
              <input 
                type="text" 
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Ask a clarifying question..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all shadow-sm"
                disabled={loadingChat}
              />
              <button type="submit" disabled={loadingChat || !chatInput.trim()} className="shrink-0 bg-blue-600 text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-sm">
                Send
              </button>
            </form>
            <button onClick={handleEnd} disabled={loadingChat} className="w-full shrink-0 bg-red-50 text-red-600 border border-red-200 py-2.5 rounded-lg text-sm font-bold hover:bg-red-100 transition-colors">
              End Interview & Evaluate
            </button>
          </div>
        </div>

      </div>

      {/* Right Panel: Editor & Output */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#1e1e1e] min-w-0">
        <div className="bg-gray-900 text-white px-4 py-2 flex justify-between items-center text-sm shadow-md shrink-0">
          <select 
            value={language} 
            onChange={e => setLanguage(e.target.value)}
            className="bg-gray-800 text-gray-300 border border-gray-700 rounded-md px-3 py-1.5 outline-none focus:border-gray-500 font-medium"
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript (Node.js)</option>
            <option value="cpp">C++ (g++)</option>
          </select>
          <button 
            onClick={runCode}
            disabled={loadingRun}
            className="shrink-0 bg-green-600 hover:bg-green-700 text-white px-5 py-1.5 rounded-md font-bold disabled:opacity-50 transition-colors flex items-center gap-2 shadow-sm"
          >
            {loadingRun ? 'Running...' : '▶ Run Code (Sends to AI)'}
          </button>
        </div>
        
        <div className="flex-1 relative min-h-0">
          <Editor
            height="100%"
            width="100%"
            language={language}
            theme="vs-dark"
            value={code}
            onChange={(val) => setCode(val || '')}
            options={{ minimap: { enabled: false }, fontSize: 14, wordWrap: "on", padding: { top: 16 } }}
          />
        </div>
        
        {/* Results Banner */}
        {result && (
          <div className={`p-4 text-sm font-mono border-t shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.1)] shrink-0 ${result.status === 'Passed' ? 'bg-green-900/90 text-green-100 border-green-700' : 'bg-red-900/90 text-red-100 border-red-700'}`}>
            <div className="flex items-start gap-3">
              <span className="text-xl shrink-0">{result.status === 'Passed' ? '✅' : '❌'}</span>
              <div className="min-w-0 overflow-hidden">
                <div className="font-bold text-base mb-1 truncate">{result.status}</div>
                <div className="whitespace-pre-wrap opacity-90 break-words max-h-32 overflow-y-auto">{result.status === 'Passed' ? 'All tests passed. The AI has been notified.' : 'Tests failed. Check chat for AI hints.'}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
