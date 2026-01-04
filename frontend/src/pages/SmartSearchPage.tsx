import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Search,
  Sparkles,
  User,
  BookOpen,
  Briefcase,
  Loader2,
  MessageSquare,
  Tag,
  MapPin,
  Calendar,
} from 'lucide-react'
import { smartSearch, type SmartSearchResponse } from '@/services/api'

// Example queries to help users get started
const EXAMPLE_QUERIES = [
  'Who works at Google?',
  'Find friends I met at the conference',
  'Colleagues with upcoming birthdays',
  'Memories from Paris',
  'People tagged as tech',
  'Engineers at startups',
  'Family members',
  'Quotes from John',
]

export function SmartSearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SmartSearchResponse | null>(null)

  const searchMutation = useMutation({
    mutationFn: smartSearch,
    onSuccess: (data) => {
      setResults(data)
    },
  })

  const handleSearch = (searchQuery: string = query) => {
    if (searchQuery.trim().length >= 3) {
      searchMutation.mutate(searchQuery)
    }
  }

  const handleExampleClick = (example: string) => {
    setQuery(example)
    handleSearch(example)
  }

  const totalResults =
    (results?.counts.persons || 0) +
    (results?.counts.anecdotes || 0) +
    (results?.counts.employments || 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-purple-500" />
          Smart Search
        </h1>
        <p className="text-muted-foreground">
          Search using natural language - just describe what you're looking for
        </p>
      </div>

      {/* Search Input */}
      <div className="bg-card border rounded-lg p-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Try: 'Who works at Google?' or 'Find friends with upcoming birthdays'"
              className="w-full pl-10 pr-4 py-3 rounded-lg border bg-background text-base focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <button
            onClick={() => handleSearch()}
            disabled={query.length < 3 || searchMutation.isPending}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {searchMutation.isPending ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                Search
              </>
            )}
          </button>
        </div>

        {/* Example Queries */}
        {!results && (
          <div className="mt-4">
            <p className="text-sm text-muted-foreground mb-2">Try these examples:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.map((example) => (
                <button
                  key={example}
                  onClick={() => handleExampleClick(example)}
                  className="px-3 py-1.5 text-sm bg-muted hover:bg-muted/80 rounded-full transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Error State */}
      {searchMutation.isError && (
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-300">
          <p className="font-medium">Search failed</p>
          <p className="text-sm">
            {searchMutation.error instanceof Error
              ? searchMutation.error.message
              : 'An error occurred while searching'}
          </p>
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Interpretation */}
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/30 dark:to-pink-950/30 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
              <MessageSquare className="h-4 w-4" />
              <span className="text-sm font-medium">Interpreted as:</span>
              <span className="text-sm">{results.interpreted_as}</span>
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              Found {totalResults} result{totalResults !== 1 ? 's' : ''} across{' '}
              {results.counts.persons > 0 && `${results.counts.persons} people`}
              {results.counts.persons > 0 && results.counts.anecdotes > 0 && ', '}
              {results.counts.anecdotes > 0 && `${results.counts.anecdotes} anecdotes`}
              {(results.counts.persons > 0 || results.counts.anecdotes > 0) &&
                results.counts.employments > 0 &&
                ', '}
              {results.counts.employments > 0 &&
                `${results.counts.employments} employment records`}
            </div>
          </div>

          {/* No Results */}
          {totalResults === 0 && (
            <div className="bg-card border rounded-lg p-12 text-center">
              <Search className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No results found</h3>
              <p className="text-muted-foreground">
                Try rephrasing your query or using different keywords
              </p>
            </div>
          )}

          {/* People Results */}
          {results.persons.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                <User className="h-5 w-5" />
                People ({results.counts.persons})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {results.persons.map((person) => (
                  <Link
                    key={person.id}
                    to={`/people/${person.id}`}
                    className="bg-card border rounded-lg p-4 hover:border-primary/50 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start gap-3">
                      {person.avatar_url ? (
                        <img
                          src={person.avatar_url}
                          alt={person.full_name}
                          className="h-12 w-12 rounded-full object-cover"
                        />
                      ) : (
                        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold">
                          {person.full_name.charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium truncate">{person.full_name}</h3>
                        {person.relationship_to_me && (
                          <p className="text-sm text-purple-600 dark:text-purple-400">
                            {person.relationship_to_me}
                          </p>
                        )}
                        {person.current_job && (
                          <p className="text-sm text-muted-foreground truncate">
                            {person.current_job}
                          </p>
                        )}
                        {person.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {person.tags.slice(0, 3).map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex items-center gap-1 px-2 py-0.5 bg-muted rounded-full text-xs"
                              >
                                <Tag className="h-3 w-3" />
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Anecdotes Results */}
          {results.anecdotes.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                <BookOpen className="h-5 w-5" />
                Anecdotes ({results.counts.anecdotes})
              </h2>
              <div className="space-y-3">
                {results.anecdotes.map((anecdote) => (
                  <div
                    key={anecdote.id}
                    className="bg-card border rounded-lg p-4 hover:border-primary/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium">{anecdote.title}</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          {anecdote.content}
                        </p>
                        <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-muted-foreground">
                          <span className="px-2 py-0.5 bg-muted rounded-full capitalize">
                            {anecdote.anecdote_type}
                          </span>
                          {anecdote.date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(anecdote.date).toLocaleDateString()}
                            </span>
                          )}
                          {anecdote.location && (
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {anecdote.location}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    {anecdote.persons.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs text-muted-foreground">
                          People: {anecdote.persons.join(', ')}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Employment Results */}
          {results.employments.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                <Briefcase className="h-5 w-5" />
                Employment Records ({results.counts.employments})
              </h2>
              <div className="bg-card border rounded-lg divide-y">
                {results.employments.map((emp) => (
                  <Link
                    key={emp.id}
                    to={`/people/${emp.person_id}`}
                    className="flex items-center gap-4 p-4 hover:bg-accent/50 transition-colors"
                  >
                    <Briefcase className="h-10 w-10 p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium">{emp.person_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {emp.title} at {emp.company}
                      </p>
                    </div>
                    {emp.is_current && (
                      <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs font-medium">
                        Current
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Search Again */}
          <div className="text-center pt-4">
            <button
              onClick={() => {
                setResults(null)
                setQuery('')
              }}
              className="text-primary hover:underline text-sm"
            >
              Clear results and search again
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
