import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export default function Settings() {
  const [name, setName] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [targetCompany, setTargetCompany] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    const res = await fetch('http://127.0.0.1:8000/api/profiles/', {
      headers: { 'Authorization': `Bearer ${session.access_token}` }
    })
    if (res.ok) {
      const data = await res.json()
      setName(data.name || '')
      setTargetRole(data.target_role || '')
      setTargetCompany(data.target_company || '')
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return

    const res = await fetch('http://127.0.0.1:8000/api/profiles/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({ name, target_role: targetRole, target_company: targetCompany })
    })

    if (res.ok) {
      setMessage('Profile updated successfully!')
    } else {
      setMessage('Failed to update profile.')
    }
    setLoading(false)
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    window.location.href = '/login'
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 mt-4">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
        <p className="text-gray-500 mt-1">Manage your account profile and interview targets.</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <form onSubmit={handleSave} className="space-y-6">
          
          {message && (
            <div className={`p-3 rounded-md text-sm ${message.includes('success') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {message}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
            <input 
              type="text" 
              value={name} 
              onChange={e => setName(e.target.value)} 
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:ring-blue-500" 
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target Role (for Mock Interviews)</label>
            <input 
              type="text" 
              value={targetRole} 
              onChange={e => setTargetRole(e.target.value)} 
              placeholder="e.g. Frontend Developer"
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:ring-blue-500" 
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target Company</label>
            <input 
              type="text" 
              value={targetCompany} 
              onChange={e => setTargetCompany(e.target.value)} 
              placeholder="e.g. Google, Meta"
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:ring-blue-500" 
            />
          </div>

          <div className="pt-4 flex items-center justify-between border-t border-gray-200">
            <button type="button" onClick={handleLogout} className="text-red-600 hover:text-red-800 text-sm font-medium">
              Sign Out
            </button>
            <button type="submit" disabled={loading} className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium">
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
