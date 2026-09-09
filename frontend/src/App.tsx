import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'

import Login from './pages/Login'
import Signup from './pages/Signup'
import DashboardLayout from './layouts/DashboardLayout'
import Dashboard from './pages/Dashboard'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { session, loading } = useAuth()
  if (loading) return <div className="p-8">Loading...</div>
  if (!session) return <Navigate to="/login" replace />
  return <>{children}</>
}

import Learning from './pages/Learning'
import Goals from './pages/Goals'
import Resume from './pages/Resume'
import Interviews from './pages/Interviews'
import Settings from './pages/Settings'
import DSAProblems from './pages/DSAProblems'
import DSAWorkspace from './pages/DSAWorkspace'
import DSAInterviewWorkspace from './pages/DSAInterviewWorkspace'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      
      <Route path="/" element={
        <ProtectedRoute>
          <DashboardLayout />
        </ProtectedRoute>
      }>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="resume" element={<Resume />} />
        <Route path="learning" element={<Learning />} />
        <Route path="goals" element={<Goals />} />
        <Route path="interview" element={<Interviews />} />
        <Route path="interview/dsa/:sessionId" element={<DSAInterviewWorkspace />} />
        <Route path="settings" element={<Settings />} />
        <Route path="dsa" element={<DSAProblems />} />
        <Route path="dsa/:id" element={<DSAWorkspace />} />
      </Route>
    </Routes>
  )
}

export default App
