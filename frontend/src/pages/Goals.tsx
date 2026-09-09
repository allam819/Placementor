import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export default function Goals() {
  const [goals, setGoals] = useState<any[]>([])
  const [newTitle, setNewTitle] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchGoals()
  }, [])

  const fetchGoals = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    const res = await fetch('http://127.0.0.1:8000/api/goals/', {
      headers: { 'Authorization': `Bearer ${session.access_token}` }
    })
    if (res.ok) setGoals(await res.json())
  }

  const addGoal = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    setLoading(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return

    const res = await fetch('http://127.0.0.1:8000/api/goals/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({ title: newTitle, goal_type: 'daily' })
    })
    
    if (res.ok) {
      setNewTitle('')
      fetchGoals()
    }
    setLoading(false)
  }

  const toggleGoal = async (id: string, currentStatus: string) => {
    const newStatus = currentStatus === 'completed' ? 'pending' : 'completed'
    // Optimistic update
    setGoals(goals.map(g => g.id === id ? { ...g, status: newStatus } : g))
    
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    await fetch(`http://127.0.0.1:8000/api/goals/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({ status: newStatus })
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Your Goals</h2>
      </div>

      <form onSubmit={addGoal} className="flex gap-2">
        <input 
          type="text"
          value={newTitle}
          onChange={e => setNewTitle(e.target.value)}
          placeholder="I want to solve 3 Leetcode questions today..."
          className="flex-1 border border-gray-300 rounded-md px-4 py-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !newTitle.trim()} className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50">
          Add Goal
        </button>
      </form>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mt-6">
        <ul className="divide-y divide-gray-200">
          {goals.map(goal => (
            <li key={goal.id} className="p-4 hover:bg-gray-50 flex items-center gap-3">
              <input 
                type="checkbox" 
                checked={goal.status === 'completed'}
                onChange={() => toggleGoal(goal.id, goal.status)}
                className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
              />
              <span className={`flex-1 ${goal.status === 'completed' ? 'line-through text-gray-400' : ''}`}>
                {goal.title}
              </span>
            </li>
          ))}
          {goals.length === 0 && (
             <li className="p-4 text-gray-500 text-center">No goals set yet!</li>
          )}
        </ul>
      </div>
    </div>
  )
}
