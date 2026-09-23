import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import Editor from '@monaco-editor/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels'
import { Play, Send, CheckCircle2, XCircle, Loader2, GripVertical, GripHorizontal, Check, AlertCircle, Bot } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { cn } from '../lib/utils'

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
  
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchSessionData()
  }, [sessionId])

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loadingChat])

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

      // 3. Fetch Messages
      const msgRes = await supabase.from('interview_messages').select('*').eq('session_id', sessionId).order('created_at')
      if (msgRes.data) {
        setMessages(msgRes.data)
      }
    }
    setLoadingChat(false)
  }

  useEffect(() => {
    if (problem && problem.starter_code) {
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
    if (!confirm("Are you sure you want to end this interview?")) return
    setLoadingChat(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/interviews/${sessionId}/evaluate`, {
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

  if (!problem) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="flex flex-col items-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
          <p className="text-gray-500 font-medium">Preparing your interview environment...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col -mx-8 -my-8 bg-surface-100 overflow-hidden text-surface-900 border-t border-gray-200">
      <PanelGroup direction="vertical" className="w-full h-full">
        
        {/* Top Half: Problem & Chat */}
        <Panel defaultSize={50} minSize={30}>
          <PanelGroup direction="horizontal">
            
            {/* Left Pane: Problem */}
            <Panel defaultSize={40} minSize={30} className="bg-white border-r border-gray-200 flex flex-col">
              <div className="px-5 py-4 border-b border-gray-100 bg-white shrink-0 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-lg font-bold text-gray-900 leading-tight">{problem.title}</h2>
                  <Badge variant={problem.difficulty === 'Easy' ? 'success' : problem.difficulty === 'Medium' ? 'warning' : 'destructive'} className="uppercase tracking-wider text-[10px]">
                    {problem.difficulty}
                  </Badge>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-5">
                <div className="prose prose-sm prose-gray max-w-none prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200 prose-pre:text-gray-900 prose-code:text-blue-700 prose-code:bg-blue-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none break-words">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{problem.description}</ReactMarkdown>
                </div>
              </div>
            </Panel>

            <PanelResizeHandle className="w-1.5 bg-gray-100 hover:bg-blue-400 active:bg-blue-600 transition-colors cursor-col-resize flex flex-col justify-center items-center">
              <GripVertical className="h-4 w-4 text-gray-400" />
            </PanelResizeHandle>

            {/* Right Pane: Interview Chat */}
            <Panel defaultSize={60} minSize={30} className="bg-gray-50 flex flex-col">
              <div className="px-5 py-4 border-b border-gray-200 bg-white shrink-0 flex items-center justify-between shadow-sm z-10">
                <div className="flex items-center gap-2">
                  <Bot className="h-5 w-5 text-blue-600" />
                  <span className="font-semibold text-gray-900">AI Interviewer</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] bg-gray-50">Stateful Context Active</Badge>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-5 space-y-6">
                {messages.map((msg, i) => {
                  const isUser = msg.role === 'user'
                  const isSystem = msg.content?.startsWith('[SYSTEM')
                  
                  if (isSystem) {
                    return (
                      <div key={i} className="flex justify-center my-4">
                        <Badge variant="secondary" className="text-[10px] font-normal text-gray-500 max-w-[80%] text-center px-3 py-1">
                          {msg.content}
                        </Badge>
                      </div>
                    )
                  }

                  const content = msg.content ? msg.content.replace(/\\n/g, '\n').replace(/\\"/g, '"') : ''
                  
                  return (
                    <div key={i} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                      <div className={cn(
                        "max-w-[85%] rounded-2xl p-4 shadow-sm",
                        isUser ? "bg-blue-600 text-white rounded-tr-sm" : "bg-white border border-gray-200 text-gray-900 rounded-tl-sm"
                      )}>
                        <div className={cn("prose prose-sm max-w-none break-words", isUser ? "prose-invert" : "prose-gray prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-100")}>
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  )
                })}
                {loadingChat && (
                   <div className="flex justify-start">
                     <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm p-4 shadow-sm flex items-center gap-3 text-gray-500">
                       <div className="flex gap-1">
                         <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                         <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                         <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                       </div>
                       <span className="text-sm italic">Thinking...</span>
                     </div>
                   </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="p-4 bg-white border-t border-gray-200 shrink-0">
                <form onSubmit={sendChatMessage} className="flex gap-2">
                  <input 
                    type="text" 
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    placeholder="Discuss your approach or ask a question..."
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                    disabled={loadingChat}
                    autoFocus
                  />
                  <Button type="submit" disabled={loadingChat || !chatInput.trim()} className="px-5">
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
              </div>
            </Panel>

          </PanelGroup>
        </Panel>

        <PanelResizeHandle className="h-1.5 bg-gray-200 hover:bg-blue-400 active:bg-blue-600 transition-colors cursor-row-resize flex justify-center items-center z-10">
           <GripHorizontal className="h-4 w-4 text-gray-400" />
        </PanelResizeHandle>

        {/* Bottom Half: Editor & Execution */}
        <Panel defaultSize={50} minSize={20} className="flex flex-col bg-[#1e1e1e]">
          <div className="bg-gray-900 border-b border-gray-800 px-4 py-2 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-4">
              <select 
                value={language} 
                onChange={e => setLanguage(e.target.value)}
                className="bg-gray-800 text-gray-200 border border-gray-700 rounded-md px-3 py-1.5 text-xs outline-none focus:border-gray-500 font-medium"
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
              </select>
              <div className="text-xs text-gray-500 font-mono hidden sm:block">Code Editor</div>
            </div>
            <div className="flex items-center gap-3">
              {result && (
                <div className="flex items-center mr-2">
                  {result.status === 'Passed' ? (
                    <Badge variant="success" className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 py-1">
                      <Check className="h-3 w-3" /> All Tests Passed
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1.5 py-1">
                      <AlertCircle className="h-3 w-3" /> Tests Failed
                    </Badge>
                  )}
                </div>
              )}
              <Button size="sm" variant="secondary" onClick={runCode} disabled={loadingRun} className="h-8 bg-gray-800 text-gray-200 hover:bg-gray-700 border border-gray-700">
                {loadingRun ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                Run Tests
              </Button>
              <Button size="sm" variant="destructive" onClick={handleEnd} className="h-8">
                End Interview
              </Button>
            </div>
          </div>

          <div className="flex-1 min-h-0 relative">
            <Editor
              height="100%"
              language={language}
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                lineHeight: 1.6,
                padding: { top: 16 },
                scrollBeyondLastLine: false,
                smoothScrolling: true,
                cursorBlinking: "smooth",
                renderLineHighlight: "all",
              }}
            />
            {loadingRun && (
              <div className="absolute inset-0 bg-gray-900/50 backdrop-blur-[1px] flex items-center justify-center z-10">
                <div className="bg-gray-800 border border-gray-700 p-4 rounded-xl shadow-2xl flex items-center gap-3 text-gray-200">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
                  <span className="font-medium text-sm">Executing code...</span>
                </div>
              </div>
            )}
          </div>
          
          {/* Execution Output Panel (Only show when there's an error) */}
          {result && result.status !== 'Passed' && (
            <div className="bg-gray-900 border-t border-gray-800 p-4 shrink-0 max-h-48 overflow-y-auto">
              <div className="text-red-400 font-mono text-sm whitespace-pre-wrap leading-relaxed">
                {result.feedback}
              </div>
            </div>
          )}
        </Panel>

      </PanelGroup>
    </div>
  )
}
