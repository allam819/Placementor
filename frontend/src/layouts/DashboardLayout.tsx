import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { supabase } from '../lib/supabase'

export default function DashboardLayout() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  const navItems = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'DSA Sandbox', path: '/dsa' },
    { label: 'Resume Analyzer', path: '/resume' },
    { label: 'Learning', path: '/learning' },
    { label: 'Goals', path: '/goals' },
    { label: 'Interviews', path: '/interview' },
    { label: 'Settings', path: '/settings' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Placement AI</h1>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`block px-3 py-2 rounded-md text-sm font-medium ${
                location.pathname === item.path
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Topbar */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
          <div className="text-sm text-gray-500">
            {/* Target Role Placeholder */}
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">{user?.email}</span>
            <button 
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-gray-900"
            >
              Log out
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-8">
          <div className="max-w-5xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
