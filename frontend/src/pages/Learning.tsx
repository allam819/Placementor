import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export default function Learning() {
  const [input, setInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  
  // Modal State
  const [selectedActivity, setSelectedActivity] = useState<any>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

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
    if (!session) return

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

  const openDetail = async (id: str) => {
    setLoadingDetail(true)
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/learning/${id}`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (res.ok) setSelectedActivity(await res.json())
    } catch (err) {}
    setLoadingDetail(false)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] relative">
      
      {/* Search Header */}
      <div className="mb-6 flex justify-between items-center gap-4">
        <h2 className="text-2xl font-bold">Learning Tracker</h2>
        <form onSubmit={handleSearch} className="flex-1 max-w-md flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search past learnings (e.g. 'How do B-Trees work?')"
            className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:ring-blue-500"
          />
          <button type="submit" disabled={isSearching} className="bg-gray-800 text-white px-4 py-2 rounded-md hover:bg-gray-900">
            {isSearching ? '...' : 'Search'}
          </button>
          {searchQuery && (
            <button type="button" onClick={() => setSearchQuery('')} className="text-sm text-gray-500 hover:text-gray-700">Clear</button>
          )}
        </form>
      </div>

      <div className="flex-1 overflow-y-auto space-y-8 pb-4 pr-2">
        {Object.entries(
          activities.reduce((acc, a) => {
            const dateStr = a.created_at ? new Date(a.created_at).toLocaleDateString('en-US', {
              weekday: 'long', month: 'short', day: 'numeric', year: 'numeric'
            }) : 'Unknown Date';
            if (!acc[dateStr]) acc[dateStr] = [];
            acc[dateStr].push(a);
            return acc;
          }, {} as Record<string, any[]>)
        ).map(([date, dayActivities]: [string, any]) => (
          <div key={date} className="space-y-4">
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider border-b pb-2">{date}</h3>
            {dayActivities.map((a: any) => (
              <div key={a.id} onClick={() => openDetail(a.id)} className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 cursor-pointer hover:border-blue-500 transition-colors">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full mb-2">
                      {a.type}
                    </span>
                    <h3 className="font-semibold text-lg">{a.title}</h3>
                    <p className="text-sm text-gray-500">{a.topic}</p>
                  </div>
                  {a.similarity && (
                    <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-md">
                      {Math.round(a.similarity * 100)}% Match
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
        {activities.length === 0 && (
          <div className="text-center text-gray-500 py-12">No activities found.</div>
        )}
      </div>

      <div className="pt-4 border-t border-gray-200">
        <form onSubmit={handleChat} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Log what you learned today..."
            className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()} className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'AI Parsing...' : 'Log'}
          </button>
        </form>
      </div>

      {/* Detail Modal Overlay */}
      {selectedActivity && (
        <div className="absolute inset-0 bg-white z-10 flex flex-col p-6 overflow-y-auto border border-gray-200 shadow-xl rounded-lg">
          <div className="flex justify-between items-start mb-6">
            <div>
               <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full mb-2">{selectedActivity.type}</span>
               <h2 className="text-3xl font-bold">{selectedActivity.title}</h2>
               <p className="text-gray-500">{selectedActivity.topic}</p>
            </div>
            <button onClick={() => setSelectedActivity(null)} className="text-gray-500 hover:text-gray-900 text-2xl font-bold">&times;</button>
          </div>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold border-b pb-2 mb-2">Description</h3>
              <p className="text-gray-700">{selectedActivity.description}</p>
            </div>
            
            {selectedActivity.content && Object.keys(selectedActivity.content).length > 0 && (
              <div>
                <h3 className="text-lg font-semibold border-b pb-2 mb-2">Structured Notes</h3>
                <div className="space-y-4">
                  {Object.entries(selectedActivity.content).map(([key, value]: [string, any]) => {
                    if (!value || (Array.isArray(value) && value.length === 0)) return null;
                    
                    const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    
                    return (
                      <div key={key}>
                        <h4 className="font-medium text-gray-800 mb-1">{formattedKey}:</h4>
                        {Array.isArray(value) ? (
                          <ul className="list-disc pl-5 text-gray-700 space-y-1">
                            {value.map((item: any, i: number) => (
                              <li key={i}>{typeof item === 'object' ? JSON.stringify(item) : item}</li>
                            ))}
                          </ul>
                        ) : typeof value === 'object' ? (
                          <pre className="bg-gray-50 p-3 rounded-md text-sm text-gray-800 whitespace-pre-wrap">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        ) : (
                          <p className="text-gray-700">{value}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            
            <div>
              <h3 className="text-lg font-semibold border-b pb-2 mb-2">Tags</h3>
              <div className="flex gap-2 flex-wrap">
                {selectedActivity.subtopics?.map((tag: string, i: number) => (
                  <span key={i} className="bg-gray-100 text-gray-700 px-2 py-1 text-xs rounded-md">{tag}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
