import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { User, Briefcase, Building, LogOut, CheckCircle2 } from 'lucide-react'

export default function Settings() {
  const [name, setName] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [targetCompany, setTargetCompany] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{text: string, type: 'success' | 'error'} | null>(null)

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
    setMessage(null)
    
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
      setMessage({ text: 'Profile updated successfully!', type: 'success' })
      setTimeout(() => setMessage(null), 3000)
    } else {
      setMessage({ text: 'Failed to update profile.', type: 'error' })
    }
    setLoading(false)
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    window.location.href = '/login'
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8 pb-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Settings</h1>
        <p className="text-gray-500">Manage your profile and career targets.</p>
      </div>

      <Card>
        <CardHeader className="border-b border-gray-100 bg-gray-50/30">
          <CardTitle className="text-lg">Profile Information</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <form onSubmit={handleSave} className="space-y-6">
            
            {message && (
              <div className={`flex items-center gap-2 p-3 rounded-md text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                {message.type === 'success' && <CheckCircle2 className="h-4 w-4" />}
                {message.text}
              </div>
            )}

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <User className="h-4 w-4 text-gray-400" /> Full Name
                </label>
                <input 
                  type="text" 
                  value={name} 
                  onChange={e => setName(e.target.value)} 
                  className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm" 
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <Briefcase className="h-4 w-4 text-gray-400" /> Target Role
                  </label>
                  <input 
                    type="text" 
                    value={targetRole} 
                    onChange={e => setTargetRole(e.target.value)} 
                    placeholder="e.g. Frontend Developer"
                    className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm" 
                  />
                  <p className="text-xs text-gray-500">Used for tailoring mock interviews.</p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <Building className="h-4 w-4 text-gray-400" /> Target Company
                  </label>
                  <input 
                    type="text" 
                    value={targetCompany} 
                    onChange={e => setTargetCompany(e.target.value)} 
                    placeholder="e.g. Google, Meta"
                    className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm" 
                  />
                </div>
              </div>
            </div>

            <div className="pt-6 flex items-center justify-between border-t border-gray-100">
              <Button type="button" variant="ghost" className="text-red-600 hover:text-red-700 hover:bg-red-50" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" /> Sign Out
              </Button>
              <Button type="submit" isLoading={loading}>
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
