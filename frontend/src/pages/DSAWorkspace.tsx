import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import Editor from '@monaco-editor/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function DSAWorkspace() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const [language, setLanguage] = useState('python')
  const [problem, setProblem] = useState<any>(null)
  const [code, setCode] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loadingRun, setLoadingRun] = useState(false)
  

  const [loadingHint, setLoadingHint] = useState(false)

  useEffect(() => {
    fetchProblem()
  }, [id])

  const fetchProblem = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return

    const res = await fetch(`http://127.0.0.1:8000/api/dsa/problems/${id}`, {
      headers: { 'Authorization': `Bearer ${session.access_token}` }
    })
    
    if (res.ok) {
      const data = await res.json()
      // Parse starter code if it's JSON
      try {
        const parsed = JSON.parse(data.starter_code)
        data.starter_code = parsed
        setCode(parsed[language] || '')
      } catch {
        // Fallback for old schema
        setCode(data.starter_code)
      }
      setProblem(data)
    }
  }

  const [chatHistory, setChatHistory] = useState<any[]>([])
  const [chatInput, setChatInput] = useState('')
  
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
        body: JSON.stringify({ problem_id: id, code, language })
      })
      
      if (res.ok) {
        setResult(await res.json())
      } else {
        setResult({ status: 'Error', feedback: 'Failed to communicate with execution server.' })
      }
    } catch (err) {
      setResult({ status: 'Error', feedback: 'Network error.' })
    }
    setLoadingRun(false)
  }
  
  const sendChatMessage = async (isHint: boolean = false) => {
    if (!isHint && !chatInput.trim()) return
    setLoadingHint(true)
    
    const newMessage = isHint ? { role: 'user', content: 'Can I get a hint based on my current code?' } : { role: 'user', content: chatInput }
    const updatedHistory = [...chatHistory, newMessage]
    setChatHistory(updatedHistory)
    if (!isHint) setChatInput('')
    
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/dsa/hint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ 
          problem_id: id, 
          code, 
          error_message: result?.feedback || null,
          chat_history: updatedHistory
        })
      })
      
      if (res.ok) {
        const data = await res.json()
        setChatHistory([...updatedHistory, { role: 'assistant', content: data.hint }])
      }
    } catch (err) {}
    setLoadingHint(false)
  }

  if (!problem) return <div className="p-8">Loading workspace...</div>

  return (
    <div className="h-[calc(100vh-4rem)] flex -m-8">
      {/* Left Panel: Problem & Chat */}
      <div className="w-1/3 border-r border-gray-200 flex flex-col bg-white">
        
        {/* Problem Description */}
        <div className="p-6 border-b border-gray-200 overflow-y-auto max-h-[50%]">
          <button onClick={() => navigate('/dsa')} className="text-blue-600 text-sm font-medium mb-4 hover:underline">&larr; Back to Problems</button>
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-xl font-bold">{problem.title}</h2>
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${
              problem.difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
              problem.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {problem.difficulty}
            </span>
          </div>
          <div className="prose prose-sm prose-gray max-w-none prose-pre:bg-gray-100 prose-pre:text-gray-900 prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1 prose-code:rounded break-words">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{problem.description ? problem.description.replace(/\\n/g, '\n').replace(/\\"/g, '"') : ''}</ReactMarkdown>
          </div>
        </div>

        {/* Results & Hints Area */}
        <div className="flex-1 p-6 overflow-y-auto bg-gray-50 flex flex-col gap-4">
          
          {result && (
            <div className={`p-4 rounded-md border ${
              result.status === 'Passed' ? 'bg-green-50 border-green-200' : 
              'bg-red-50 border-red-200'
            }`}>
              <h3 className={`font-bold ${result.status === 'Passed' ? 'text-green-800' : 'text-red-800'}`}>
                {result.status}
              </h3>
              <pre className="mt-2 text-xs text-gray-800 whitespace-pre-wrap">{result.feedback}</pre>
              {result.execution_time_ms && <p className="mt-2 text-xs text-gray-500">Execution Time: {result.execution_time_ms}ms</p>}
            </div>
          )}
          
          {(result && result.status !== 'Passed') && (
            <button onClick={() => sendChatMessage(true)} disabled={loadingHint} className="bg-purple-100 text-purple-800 border border-purple-200 px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-200 disabled:opacity-50 text-left flex justify-between items-center shrink-0">
              <span>{loadingHint ? 'AI is analyzing your code...' : 'Ask AI for a Hint'}</span>
              <span>✨</span>
            </button>
          )}

          <div className="flex-1 overflow-y-auto space-y-4">
            {chatHistory.map((msg, i) => {
              const content = msg.content ? msg.content.replace(/\\n/g, '\n').replace(/\\"/g, '"') : ''
              return (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`p-3 rounded-xl max-w-[85%] text-sm shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'}`}>
                    {msg.role === 'assistant' && <div className="text-xs text-gray-500 mb-2 font-bold uppercase tracking-wider">AI Interviewer</div>}
                    <div className={`prose prose-sm max-w-none break-words ${msg.role === 'user' ? 'prose-invert' : ''}`}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              )
            })}
            {loadingHint && chatHistory.length > 0 && chatHistory[chatHistory.length-1].role === 'user' && (
              <div className="text-sm text-gray-500 animate-pulse">AI is typing...</div>
            )}
          </div>

          <form onSubmit={e => { e.preventDefault(); sendChatMessage(false) }} className="mt-2 flex gap-2 shrink-0">
            <input 
              type="text" 
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder="Ask a clarifying question..."
              className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500"
              disabled={loadingHint}
            />
            <button type="submit" disabled={loadingHint || !chatInput.trim()} className="bg-gray-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-800 disabled:opacity-50">
              Send
            </button>
          </form>
          
        </div>
      </div>

      {/* Right Panel: Editor */}
      <div className="w-2/3 flex flex-col">
        <div className="bg-gray-900 text-white px-4 py-2 flex justify-between items-center text-sm">
          <select 
            value={language} 
            onChange={e => setLanguage(e.target.value)}
            className="bg-gray-800 text-gray-300 border border-gray-700 rounded px-2 py-1 outline-none focus:border-gray-500"
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript (Node.js)</option>
            <option value="cpp">C++ (g++)</option>
          </select>
          <button 
            onClick={runCode}
            disabled={loadingRun}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-1 rounded font-medium disabled:opacity-50"
          >
            {loadingRun ? 'Running...' : 'Run Code'}
          </button>
        </div>
        <div className="flex-1">
          <Editor
            height="100%"
            language={language}
            theme="vs-dark"
            value={code}
            onChange={(val) => setCode(val || '')}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              wordWrap: "on"
            }}
          />
        </div>
      </div>
    </div>
  )
}
