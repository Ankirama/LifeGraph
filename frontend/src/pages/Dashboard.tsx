import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Users,
  BookOpen,
  Camera,
  Heart,
  Cake,
  Plus,
  Sparkles,
  ArrowRight,
  Gift,
  MessageSquare,
  Quote,
  Smile,
  StickyNote,
} from 'lucide-react'
import { getDashboard } from '@/services/api'

const anecdoteIcons: Record<string, typeof MessageSquare> = {
  memory: MessageSquare,
  quote: Quote,
  joke: Smile,
  note: StickyNote,
}

export function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-destructive">Failed to load dashboard. Make sure the backend is running.</p>
        </div>
      </div>
    )
  }

  const stats = [
    { name: 'People', value: data?.stats.total_persons || 0, icon: Users, href: '/people' },
    { name: 'Relationships', value: data?.stats.total_relationships || 0, icon: Heart, href: '/relationships' },
    { name: 'Anecdotes', value: data?.stats.total_anecdotes || 0, icon: BookOpen, href: '/anecdotes' },
    { name: 'Photos', value: data?.stats.total_photos || 0, icon: Camera, href: '/photos' },
  ]

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const formatDaysUntil = (days: number) => {
    if (days === 0) return 'Today!'
    if (days === 1) return 'Tomorrow'
    return `In ${days} days`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-muted-foreground">
            Welcome to LifeGraph, your personal relationship memory.
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/people"
            className="inline-flex items-center gap-2 border px-4 py-2 rounded-md text-sm font-medium hover:bg-accent"
          >
            <Sparkles className="h-4 w-4" />
            AI Import
          </Link>
          <Link
            to="/people"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Add Person
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Link
            key={stat.name}
            to={stat.href}
            className="bg-card border rounded-lg p-4 flex items-center gap-4 hover:border-primary transition-colors"
          >
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <stat.icon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.name}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Birthdays */}
        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Cake className="h-5 w-5 text-pink-500" />
              Upcoming Birthdays
            </h3>
          </div>

          {data?.upcoming_birthdays && data.upcoming_birthdays.length > 0 ? (
            <div className="space-y-3">
              {data.upcoming_birthdays.slice(0, 5).map((birthday) => (
                <Link
                  key={birthday.id}
                  to={`/people/${birthday.id}`}
                  className="flex items-center justify-between p-2 -mx-2 rounded-md hover:bg-accent"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center">
                      <Gift className="h-4 w-4 text-pink-600 dark:text-pink-400" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{birthday.full_name}</p>
                      <p className="text-xs text-muted-foreground">
                        Turning {birthday.turning_age} on {formatDate(birthday.date)}
                      </p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    birthday.days_until === 0
                      ? 'bg-pink-100 text-pink-700 dark:bg-pink-900/50 dark:text-pink-300'
                      : birthday.days_until <= 7
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300'
                        : 'bg-muted text-muted-foreground'
                  }`}>
                    {formatDaysUntil(birthday.days_until)}
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground text-sm">
              <Cake className="h-8 w-8 mx-auto mb-2 opacity-50" />
              No upcoming birthdays in the next 30 days
            </div>
          )}
        </div>

        {/* Recent Anecdotes */}
        <div className="bg-card border rounded-lg p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-blue-500" />
              Recent Anecdotes
            </h3>
            {data?.recent_anecdotes && data.recent_anecdotes.length > 0 && (
              <Link
                to="/anecdotes"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                View all
                <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>

          {data?.recent_anecdotes && data.recent_anecdotes.length > 0 ? (
            <div className="space-y-3">
              {data.recent_anecdotes.slice(0, 5).map((anecdote) => {
                const Icon = anecdoteIcons[anecdote.anecdote_type] || StickyNote
                return (
                  <div
                    key={anecdote.id}
                    className="p-3 border rounded-lg hover:border-primary/50 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
                        <Icon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {anecdote.title && (
                            <span className="font-medium text-sm truncate">{anecdote.title}</span>
                          )}
                          <span className="text-xs text-muted-foreground capitalize">
                            {anecdote.anecdote_type}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {anecdote.content}
                        </p>
                        {anecdote.persons.length > 0 && (
                          <p className="text-xs text-primary mt-1">
                            About: {anecdote.persons.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground text-sm">
              <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
              No anecdotes yet. Start by adding memories about your contacts!
            </div>
          )}
        </div>
      </div>

      {/* Secondary Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recently Added People */}
        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Users className="h-5 w-5 text-green-500" />
              Recently Added
            </h3>
            {data?.recent_persons && data.recent_persons.length > 0 && (
              <Link
                to="/people"
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                View all
                <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>

          {data?.recent_persons && data.recent_persons.length > 0 ? (
            <div className="space-y-2">
              {data.recent_persons.slice(0, 5).map((person) => (
                <Link
                  key={person.id}
                  to={`/people/${person.id}`}
                  className="flex items-center justify-between p-2 -mx-2 rounded-md hover:bg-accent"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-green-600 dark:text-green-400 font-medium text-sm">
                      {person.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{person.full_name}</p>
                      {person.relationship_to_me && (
                        <p className="text-xs text-muted-foreground capitalize">
                          {person.relationship_to_me}
                        </p>
                      )}
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground text-sm">
              <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
              No people added yet.
              <Link to="/people" className="text-primary hover:underline block mt-1">
                Add your first contact
              </Link>
            </div>
          )}
        </div>

        {/* Relationship Distribution */}
        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Heart className="h-5 w-5 text-red-500" />
              Relationship Types
            </h3>
          </div>

          {data?.relationship_distribution && data.relationship_distribution.length > 0 ? (
            <div className="space-y-3">
              {data.relationship_distribution.map((rel, index) => {
                const maxCount = data.relationship_distribution[0]?.count || 1
                const percentage = (rel.count / maxCount) * 100
                return (
                  <div key={rel.name} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="capitalize">{rel.name}</span>
                      <span className="text-muted-foreground">{rel.count}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground text-sm">
              <Heart className="h-8 w-8 mx-auto mb-2 opacity-50" />
              No relationships yet. Add connections between your contacts!
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
