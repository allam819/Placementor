import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export default function Dashboard() {
  const [profile, setProfile] = useState<any>(null)
  const [latestResume, setLatestResume] = useState<any>(null)
  const [goals, setGoals] = useState<any[]>([])
  const [learning, setLearning] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return

    try {
      // Fetch Profile
      const profileRes = await fetch('http://127.0.0.1:8000/api/profiles/', {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      })
      if (profileRes.ok) setProfile(await profileRes.json())

      // Fetch Latest Resume Analysis
      const { data: resumeData } = await supabase
        .from('resume_analyses')
        .select('overall_score, gaps')
        .eq('user_id', session.user.id)
        .order('created_at', { ascending: false })
        .limit(1)
      if (resumeData && resumeData.length > 0) setLatestResume(resumeData[0])

      // Fetch Goals
      const { data: goalsData } = await supabase
        .from('goals')
        .select('*')
        .eq('user_id', session.user.id)
        .eq('status', 'pending')
        .order('target_date', { ascending: true })
        .limit(3)
      if (goalsData) setGoals(goalsData)

      // Fetch Recent Learning
      const { data: learningData } = await supabase
        .from('learning_activities')
        .select('*')
        .eq('user_id', session.user.id)
        .order('created_at', { ascending: false })
        .limit(3)
      if (learningData) setLearning(learningData)
    } catch (e) {
      console.error('Dashboard fetch error:', e)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-8">Loading Dashboard...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Preparation Profile */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Current Preparation Profile</h3>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500">Target Role</p>
              <p className="font-medium">{profile?.target_role || 'Not set'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Target Company</p>
              <p className="font-medium text-gray-400">{profile?.target_company || 'Not set'}</p>
            </div>
          </div>
        </div>

        {/* Resume Status */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Latest Resume Match</h3>
          {latestResume ? (
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Match Score</span>
                <span className="text-2xl font-bold text-blue-600">{latestResume.overall_score}%</span>
              </div>
              <div className="pt-2 text-sm text-gray-600 space-y-1">
                <p>Identified Gaps: {latestResume.gaps.length}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No resumes analyzed yet.</p>
          )}
        </div>

        {/* Today's Goals */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Pending Goals</h3>
          {goals.length > 0 ? (
            <div className="space-y-3">
              {goals.map(goal => (
                <label key={goal.id} className="flex items-center space-x-3 text-sm">
                  <input type="checkbox" className="rounded border-gray-300 text-blue-600" disabled />
                  <span>{goal.title}</span>
                </label>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No pending goals.</p>
          )}
        </div>

        {/* Recent Learning */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Recent Learning</h3>
          {learning.length > 0 ? (
            <div className="space-y-4">
              {learning.map(activity => (
                <div key={activity.id} className="border-l-2 border-blue-500 pl-4">
                  <p className="text-xs text-gray-500">{new Date(activity.created_at).toLocaleDateString()}</p>
                  <p className="font-medium text-sm">{activity.topic} ({activity.type})</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No learning activities logged.</p>
          )}
        </div>
      </div>
    </div>
  )
}
