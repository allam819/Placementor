import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { Card } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { EmptyState } from '../components/ui/empty-state'
import { Target, Plus, CheckCircle2, Circle } from 'lucide-react'
import { cn } from '../lib/utils'

export default function Goals() {
  const [goals, setGoals] = useState<any[]>([])
  const [newTitle, setNewTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)

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
    setFetching(false)
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

  const pendingGoals = goals.filter(g => g.status !== 'completed')
  const completedGoals = goals.filter(g => g.status === 'completed')

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-10">
      <div className="flex flex-col gap-2 mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Preparation Goals</h1>
        <p className="text-gray-500">Track your daily and weekly preparation milestones.</p>
      </div>

      <Card className="p-2 bg-gray-50/50">
        <form onSubmit={addGoal} className="flex gap-2">
          <input 
            type="text"
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            placeholder="E.g. Solve 3 Medium Graph problems..."
            className="flex-1 bg-white border border-gray-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
            disabled={loading}
          />
          <Button type="submit" disabled={loading || !newTitle.trim()} isLoading={loading}>
            <Plus className="mr-2 h-4 w-4" /> Add Goal
          </Button>
        </form>
      </Card>

      {!fetching && goals.length === 0 ? (
        <Card className="border-dashed">
          <EmptyState 
            icon={Target}
            title="No goals set yet"
            description="Create your first goal using the input above to stay on track."
          />
        </Card>
      ) : (
        <div className="space-y-6">
          {pendingGoals.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Pending Goals</h3>
              <div className="space-y-2">
                {pendingGoals.map(goal => (
                  <Card key={goal.id} className="transition-all hover:border-blue-200 hover:shadow-sm">
                    <div 
                      className="p-4 flex items-center gap-4 cursor-pointer group"
                      onClick={() => toggleGoal(goal.id, goal.status)}
                    >
                      <button className="text-gray-300 group-hover:text-blue-500 transition-colors focus:outline-none shrink-0">
                        <Circle className="h-5 w-5" />
                      </button>
                      <span className="text-sm font-medium text-gray-900 leading-tight">
                        {goal.title}
                      </span>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {completedGoals.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Completed</h3>
              <div className="space-y-2">
                {completedGoals.map(goal => (
                  <Card key={goal.id} className="bg-gray-50/50 border-gray-100">
                    <div 
                      className="p-4 flex items-center gap-4 cursor-pointer group opacity-75 hover:opacity-100 transition-opacity"
                      onClick={() => toggleGoal(goal.id, goal.status)}
                    >
                      <button className="text-emerald-500 transition-colors focus:outline-none shrink-0">
                        <CheckCircle2 className="h-5 w-5" />
                      </button>
                      <span className="text-sm font-medium text-gray-500 line-through leading-tight">
                        {goal.title}
                      </span>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
