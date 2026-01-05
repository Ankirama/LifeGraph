import { Outlet, Link, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  LayoutDashboard,
  Users,
  Link2,
  Network,
  BookOpen,
  Image,
  Tags,
  FolderTree,
  Settings,
  UserCircle,
  MessageSquare,
  Sparkles,
  Download,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { GlobalSearch } from './GlobalSearch'
import { getMe } from '@/services/api'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'AI Chat', href: '/chat', icon: MessageSquare },
  { name: 'Smart Search', href: '/search', icon: Sparkles },
  { name: 'People', href: '/people', icon: Users },
  { name: 'Relationships', href: '/relationships', icon: Link2 },
  { name: 'Graph', href: '/graph', icon: Network },
  { name: 'Anecdotes', href: '/anecdotes', icon: BookOpen },
  { name: 'Photos', href: '/photos', icon: Image },
  { name: 'Groups', href: '/groups', icon: FolderTree },
  { name: 'Tags', href: '/tags', icon: Tags },
  { name: 'Export', href: '/export', icon: Download },
  { name: 'My Profile', href: '/me', icon: UserCircle },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Layout() {
  const location = useLocation()

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card">
        <div className="flex h-16 items-center px-6 border-b">
          <h1 className="text-xl font-bold">LifeGraph</h1>
        </div>
        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b bg-card flex items-center justify-between px-6">
          <div className="flex items-center gap-4 flex-1">
            <GlobalSearch />
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/me"
              className="flex items-center gap-2 hover:bg-accent rounded-md px-2 py-1 transition-colors"
            >
              <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
                {me?.first_name?.charAt(0).toUpperCase() || 'U'}
              </div>
              {me && (
                <span className="text-sm font-medium">{me.full_name}</span>
              )}
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
