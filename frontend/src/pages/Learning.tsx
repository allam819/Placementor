import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { Card, CardContent } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { EmptyState } from '../components/ui/empty-state'
import { Search, Plus, BookOpen, X, Clock, BrainCircuit } from 'lucide-react'
import { cn } from '../lib/utils'

export default function Learning() {
  const [input, setInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [selectedActivity, setSelectedActivity] = useState<any>(null)

  useEffect(() => {
    if (!searchQuery) {
      fetchRecent()
    }
  }, [searchQuery])

  const fetchRecent = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return

    try {
      const res = await fetch('http://127.0.0.1:8000/api/learning/recent', {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (res.ok) setActivities(await res.json())
    } catch (err) {}
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    
    setIsSearching(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return setIsSearching(false)

    try {
      const res = await fetch('http://127.0.0.1:8000/api/learning/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ query: searchQuery, match_threshold: 0.2, match_count: 5 })
      })
      if (res.ok) {
        setActivities(await res.json())
      }
    } catch (err) {}
    setIsSearching(false)
  }

  const handleChat = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    setLoading(true)
    
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return setLoading(false)

    try {
      const res = await fetch('http://127.0.0.1:8000/api/learning/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ message: input })
      })
      if (res.ok) {
        const data = await res.json()
        if (!searchQuery) setActivities([data.data, ...activities])
        setInput('')
      }
    } catch (err) {}
    setLoading(false)
  }

  const openDetail = async (id: string) => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/learning/${id}`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (res.ok) setSelectedActivity(await res.json())
    } catch (err) {}
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] relative max-w-5xl mx-auto pb-4">
      
      {/* Header and Controls */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">Learning Library</h1>
        <p className="text-gray-500 mb-6">Track your study progress and easily retrieve past concepts via semantic search.</p>
        
        <div className="flex flex-col md:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search concepts, algorithms, tools..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow shadow-sm"
            />
          </form>
          
          <form onSubmit={handleChat} className="flex-1 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="E.g. I just learned about PostgreSQL indexing..."
              className="flex-1 bg-white border border-gray-200 px-4 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow shadow-sm disabled:opacity-50"
              disabled={loading}
            />
            <Button type="submit" disabled={loading || !input.trim()} isLoading={loading} className="shrink-0">
              <Plus className="mr-2 h-4 w-4" /> Add Note
            </Button>
          </form>
        </div>
      </div>

      {/* Activity List */}
      <div className="flex-1 overflow-y-auto pr-2 pb-4 space-y-3">
        {isSearching && activities.length === 0 ? (
          <div className="py-12 text-center text-sm text-gray-500">Searching...</div>
        ) : activities.length > 0 ? (
          activities.map((a: any) => (
            <Card 
              key={a.id} 
              className="group cursor-pointer hover:border-blue-300 hover:shadow-md transition-all duration-200"
              onClick={() => openDetail(a.id)}
            >
              <CardContent className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex gap-4 items-start">
                  <div className="mt-1 bg-blue-50 text-blue-600 p-2.5 rounded-lg shrink-0 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                    <BrainCircuit className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 leading-tight">{a.title}</h3>
                      {a.similarity && (
                        <Badge variant="success" className="text-[10px] ml-2">
                          {Math.round(a.similarity * 100)}% Match
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-1">{a.topic}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3"/> {new Date(a.created_at).toLocaleDateString()}</span>
                      <span className="capitalize px-1.5 py-0.5 bg-gray-100 rounded text-gray-600 font-medium">{a.type?.replace('_', ' ')}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card className="h-full border-dashed">
            <EmptyState 
              icon={BookOpen}
              title={searchQuery ? "No results found" : "Your library is empty"}
              description={searchQuery ? "Try a different search term." : "Use the input above to quickly log new concepts you learn."}
            />
          </Card>
        )}
      </div>

      {/* Detail Modal Overlay */}
      {selectedActivity && (
        <div className="absolute inset-0 z-50 flex items-center justify-center p-4 sm:p-6 animate-in">
          <div className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm rounded-xl" onClick={() => setSelectedActivity(null)} />
          <Card className="relative w-full max-w-3xl max-h-full flex flex-col shadow-2xl">
            <div className="flex items-start justify-between p-6 border-b border-gray-100 shrink-0">
              <div>
                <Badge variant="secondary" className="mb-3 uppercase tracking-wider text-[10px]">
                  {selectedActivity.type?.replace('_', ' ')}
                </Badge>
                <h2 className="text-2xl font-bold text-gray-900 leading-tight">{selectedActivity.title}</h2>
                <p className="text-sm text-gray-500 mt-1">{selectedActivity.topic}</p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setSelectedActivity(null)} className="-mt-2 -mr-2 shrink-0">
                <X className="h-5 w-5 text-gray-400" />
              </Button>
            </div>
            
            <div className="p-6 overflow-y-auto space-y-8 text-sm">
              <section>
                <h3 className="font-semibold text-gray-900 mb-2 uppercase tracking-wider text-xs">Description</h3>
                <p className="text-gray-700 leading-relaxed">{selectedActivity.description}</p>
              </section>
              
              {selectedActivity.content && Object.keys(selectedActivity.content).length > 0 && (
                <section>
                  <h3 className="font-semibold text-gray-900 mb-3 uppercase tracking-wider text-xs">Structured Notes</h3>
                  <div className="space-y-4">
                    {Object.entries(selectedActivity.content).map(([key, value]: [string, any]) => {
                      if (!value || (Array.isArray(value) && value.length === 0)) return null;
                      const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                      
                      return (
                        <div key={key} className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                          <h4 className="font-semibold text-gray-800 mb-2">{formattedKey}</h4>
                          {Array.isArray(value) ? (
                            <ul className="space-y-1.5 pl-4 list-disc marker:text-gray-300">
                              {value.map((item: any, i: number) => (
                                <li key={i} className="text-gray-700 pl-1">{typeof item === 'object' ? JSON.stringify(item) : item}</li>
                              ))}
                            </ul>
                          ) : typeof value === 'object' ? (
                            <pre className="bg-white p-3 rounded border border-gray-200 text-xs text-gray-800 whitespace-pre-wrap overflow-x-auto">
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          ) : (
                            <p className="text-gray-700">{value}</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}
              
              {selectedActivity.subtopics && selectedActivity.subtopics.length > 0 && (
                <section>
                  <h3 className="font-semibold text-gray-900 mb-3 uppercase tracking-wider text-xs">Tags</h3>
                  <div className="flex gap-2 flex-wrap">
                    {selectedActivity.subtopics.map((tag: string, i: number) => (
                      <span key={i} className="bg-gray-100 text-gray-600 border border-gray-200 px-2.5 py-1 text-xs rounded-md">
                        {tag}
                      </span>
                    ))}
                  </div>
                </section>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
