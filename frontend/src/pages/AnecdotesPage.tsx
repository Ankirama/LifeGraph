import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, BookOpen, Calendar, MapPin, User, Search } from 'lucide-react'
import { getAnecdotes } from '@/services/api'
import { format } from 'date-fns'
import type { Anecdote } from '@/types'

const ANECDOTE_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'memory', label: 'Memory' },
  { value: 'joke', label: 'Joke' },
  { value: 'quote', label: 'Quote' },
  { value: 'note', label: 'Note' },
]

const TYPE_COLORS: Record<string, string> = {
  memory: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  joke: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  quote: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  note: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
}

export function AnecdotesPage() {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  const { data: anecdotesResponse, isLoading } = useQuery({
    queryKey: ['anecdotes', { search, anecdote_type: typeFilter }],
    queryFn: () =>
      getAnecdotes({
        search: search || undefined,
        anecdote_type: typeFilter || undefined,
      }),
  })

  const anecdotes = anecdotesResponse?.results || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Anecdotes</h1>
          <p className="text-muted-foreground">
            Memories, jokes, quotes, and notes about people
          </p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90">
          <Plus className="h-4 w-4" />
          Add Anecdote
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search anecdotes..."
            className="w-full pl-9 pr-4 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {ANECDOTE_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="text-muted-foreground">Loading anecdotes...</div>
      ) : anecdotes.length === 0 ? (
        <div className="bg-card border rounded-lg p-12 text-center">
          <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No anecdotes yet</h3>
          <p className="text-muted-foreground mb-4">
            Start capturing memories, jokes, and notes about the people in your life
          </p>
          <button className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90">
            <Plus className="h-4 w-4" />
            Add your first anecdote
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {anecdotes.map((anecdote) => (
            <AnecdoteCard key={anecdote.id} anecdote={anecdote} />
          ))}
        </div>
      )}
    </div>
  )
}

function AnecdoteCard({ anecdote }: { anecdote: Anecdote }) {
  return (
    <div className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Type badge and title */}
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded-full capitalize ${
                TYPE_COLORS[anecdote.anecdote_type] || TYPE_COLORS.note
              }`}
            >
              {anecdote.anecdote_type}
            </span>
            {anecdote.title && (
              <h3 className="font-medium truncate">{anecdote.title}</h3>
            )}
          </div>

          {/* Content */}
          <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
            {anecdote.content}
          </p>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            {anecdote.date && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {format(new Date(anecdote.date), 'MMM d, yyyy')}
              </span>
            )}
            {anecdote.location && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {anecdote.location}
              </span>
            )}
            {anecdote.persons.length > 0 && (
              <span className="flex items-center gap-1">
                <User className="h-3.5 w-3.5" />
                {anecdote.persons.map((person, idx) => (
                  <span key={person.id}>
                    <Link
                      to={`/people/${person.id}`}
                      className="hover:text-primary hover:underline"
                    >
                      {person.full_name}
                    </Link>
                    {idx < anecdote.persons.length - 1 && ', '}
                  </span>
                ))}
              </span>
            )}
          </div>

          {/* Tags */}
          {anecdote.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-3">
              {anecdote.tags.map((tag) => (
                <span
                  key={tag.id}
                  className="px-2 py-0.5 text-xs rounded-full"
                  style={{ backgroundColor: tag.color + '20', color: tag.color }}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
