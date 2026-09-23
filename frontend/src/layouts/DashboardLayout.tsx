import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { supabase } from '../lib/supabase'
import { 
  LayoutDashboard, 
  Code2, 
  FileText, 
  GraduationCap, 
  Target, 
  MessageSquare, 
  Settings, 
  LogOut,
  User,
  Menu,
  X
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '../lib/utils'

export default function DashboardLayout() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate('/login')
  }

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Resume', path: '/resume', icon: FileText },
    { label: 'Learning', path: '/learning', icon: GraduationCap },
    { label: 'Interviews', path: '/interview', icon: MessageSquare },
    { label: 'DSA Sandbox', path: '/dsa', icon: Code2 },
    { label: 'Goals', path: '/goals', icon: Target },
  ]

  const bottomNavItems = [
    { label: 'Settings', path: '/settings', icon: Settings },
  ]

  const NavLinks = ({ items, onClick }: { items: typeof navItems, onClick?: () => void }) => (
    <>
      {items.map(item => {
        const Icon = item.icon
        const isActive = location.pathname.startsWith(item.path)
        
        return (
          <Link
            key={item.path}
            to={item.path}
            onClick={onClick}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              isActive 
                ? "bg-gray-100 text-gray-900" 
                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            )}
          >
            <Icon className={cn("h-4 w-4", isActive ? "text-gray-900" : "text-gray-500")} />
            {item.label}
          </Link>
        )
      })}
    </>
  )

  return (
    <div className="flex h-screen bg-surface-50 overflow-hidden text-surface-900">
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-900/50 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 flex flex-col transform transition-transform duration-200 ease-in-out lg:static lg:translate-x-0",
        isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="h-16 flex items-center px-6 border-b border-gray-200/60">
          <div className="flex items-center gap-2 font-bold text-lg tracking-tight">
            <div className="bg-blue-600 w-6 h-6 rounded-md flex items-center justify-center">
              <span className="text-white text-xs">P</span>
            </div>
            Placementor
          </div>
          <button 
            className="ml-auto lg:hidden text-gray-500 hover:text-gray-900"
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="flex-1 flex flex-col justify-between p-3 overflow-y-auto">
          <nav className="space-y-0.5">
            <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
              Menu
            </div>
            <NavLinks items={navItems} onClick={() => setIsMobileMenuOpen(false)} />
          </nav>
          
          <nav className="space-y-0.5 mt-8">
             <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
              Account
            </div>
            <NavLinks items={bottomNavItems} onClick={() => setIsMobileMenuOpen(false)} />
          </nav>
        </div>

        {/* User Profile Footer */}
        <div className="p-4 border-t border-gray-200/60 flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
            <User className="h-4 w-4 text-gray-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user?.email?.split('@')[0]}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {user?.email}
            </p>
          </div>
          <button 
            onClick={handleLogout}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
            title="Log out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="h-14 bg-white border-b border-gray-200 flex items-center px-4 lg:hidden shrink-0">
          <button 
            onClick={() => setIsMobileMenuOpen(true)}
            className="p-2 -ml-2 mr-2 text-gray-600 hover:text-gray-900 rounded-md"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="font-semibold text-gray-900">Placementor</div>
        </header>

        {/* Page Content Scrollable Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="w-full max-w-6xl mx-auto p-4 md:p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
