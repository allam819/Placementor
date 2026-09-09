import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useNavigate } from 'react-router-dom'

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
    if (!window.confirm("Are you sure you want to delete this problem?")) return
    
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/dsa/problems/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (res.ok) {
        setProblems(problems.filter(p => p.id !== id))
      }
    } catch (err) {}
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 mt-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">DSA Practice</h2>
        <div className="flex gap-2">
          <button onClick={() => generateProblem('Easy')} disabled={generating} className="bg-green-100 text-green-800 px-3 py-1 rounded hover:bg-green-200 text-sm font-medium disabled:opacity-50">
            + Random Easy
          </button>
          <button onClick={() => generateProblem('Medium')} disabled={generating} className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded hover:bg-yellow-200 text-sm font-medium disabled:opacity-50">
            + Random Medium
          </button>
          <button onClick={() => generateProblem('Hard')} disabled={generating} className="bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200 text-sm font-medium disabled:opacity-50">
            {generating ? 'Generating...' : '+ Random Hard'}
          </button>
        </div>
      </div>
      
      {loading ? (
        <p>Loading problems...</p>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <ul className="divide-y divide-gray-200">
            {problems.map(prob => (
              <li key={prob.id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-lg">{prob.title}</h3>
                    {prob.solved && (
                      <span className="text-xs font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                        ✓ Solved
                      </span>
                    )}
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full inline-block mt-2 ${
                    prob.difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
                    prob.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {prob.difficulty}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <button 
                    onClick={(e) => deleteProblem(e, prob.id)}
                    className="text-red-500 hover:text-red-700 text-sm font-medium px-2 py-2"
                  >
                    Delete
                  </button>
                  <button 
                    onClick={() => navigate(`/dsa/${prob.id}`)}
                    className="bg-gray-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-800"
                  >
                    {prob.solved ? 'Review' : 'Solve'}
                  </button>
                </div>
              </li>
            ))}
            {problems.length === 0 && (
              <li className="p-8 text-center text-gray-500">No problems generated yet.</li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
