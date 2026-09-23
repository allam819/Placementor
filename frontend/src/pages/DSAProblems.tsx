import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { EmptyState } from '../components/ui/empty-state'
import { Code2, Play, Trash2, Loader2, Sparkles } from 'lucide-react'

export default function DSAProblems() {
  const [problems, setProblems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetchProblems()
  }, [])

  const fetchProblems = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return

    try {
      const res = await fetch('http://127.0.0.1:8000/api/dsa/problems', {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (res.ok) setProblems(await res.json())
    } catch (err) {}
    setLoading(false)
  }

  const generateProblem = async (difficulty: string) => {
    setGenerating(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/dsa/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ difficulty })
      })
      if (res.ok) {
        const newProb = await res.json()
        navigate(`/dsa/${newProb.id}`)
      }
    } catch (err) {}
    setGenerating(false)
  }

  const deleteProblem = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      await fetch(`http://127.0.0.1:8000/api/dsa/problems/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      fetchProblems()
    } catch (err) {}
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-10">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">DSA Sandbox</h1>
          <p className="text-gray-500">Practice standalone algorithmic problems generated dynamically.</p>
        </div>
        <div className="flex items-center gap-2">
          {['Easy', 'Medium', 'Hard'].map(diff => (
            <Button 
              key={diff} 
              variant="outline" 
              onClick={() => generateProblem(diff)} 
              disabled={generating}
              className="bg-white"
            >
              {generating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4 text-blue-500" />}
              {diff}
            </Button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      ) : problems.length === 0 ? (
        <Card className="border-dashed">
          <EmptyState 
            icon={Code2}
            title="No problems generated"
            description="Use the buttons above to generate an AI-tailored DSA problem."
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {problems.map(prob => (
            <Card 
              key={prob.id} 
              className="group cursor-pointer hover:border-blue-300 hover:shadow-md transition-all"
              onClick={() => navigate(`/dsa/${prob.id}`)}
            >
              <CardContent className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="bg-blue-50 text-blue-600 p-3 rounded-lg shrink-0 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                    <Code2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg leading-tight mb-1">{prob.title}</h3>
                    <div className="flex items-center gap-3">
                      <Badge variant={prob.difficulty === 'Easy' ? 'success' : prob.difficulty === 'Medium' ? 'warning' : 'destructive'} className="text-[10px] uppercase">
                        {prob.difficulty}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(prob.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button variant="ghost" size="icon" onClick={(e) => deleteProblem(e, prob.id)} className="text-gray-400 hover:text-red-600 hover:bg-red-50">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                  <Button size="sm" className="ml-2">
                    <Play className="h-4 w-4 mr-2" /> Solve
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
