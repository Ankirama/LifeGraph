import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Search, User, BookOpen, X } from 'lucide-react'
import { globalSearch } from '@/services/api'

export function GlobalSearch() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['globalSearch', query],
    queryFn: () => globalSearch(query),
    enabled: query.length >= 2,
    staleTime: 1000 * 60, // 1 minute
  })

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to focus search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
        setIsOpen(true)
      }
      // Escape to close
      if (e.key === 'Escape') {
        setIsOpen(false)
        inputRef.current?.blur()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleSelect = (type: 'person' | 'anecdote', id: string) => {
    setIsOpen(false)
    setQuery('')
    if (type === 'person') {
      navigate(`/people/${id}`)
    } else {
      // For anecdotes, navigate to the anecdotes page with this one highlighted
      navigate(`/anecdotes?highlight=${id}`)
    }
  }

  const hasResults =
    (data?.persons && data.persons.length > 0) ||
    (data?.anecdotes && data.anecdotes.length > 0)

  return (
    <div ref={containerRef} className="relative max-w-md w-full">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setIsOpen(true)
        }}
        onFocus={() => setIsOpen(true)}
        placeholder="Search people, anecdotes... (⌘K)"
        className="w-full pl-10 pr-10 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
      {query && (
        <button
          onClick={() => {
            setQuery('')
            inputRef.current?.focus()
          }}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 hover:bg-accent rounded"
        >
          <X className="h-4 w-4 text-muted-foreground" />
        </button>
      )}

      {/* Results Dropdown */}
      {isOpen && query.length >= 2 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-popover border rounded-md shadow-lg z-50 max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-sm text-muted-foreground">Searching...</div>
          ) : !hasResults ? (
            <div className="p-4 text-sm text-muted-foreground">
              No results found for "{query}"
            </div>
          ) : (
            <div className="py-2">
              {/* People Results */}
              {data?.persons && data.persons.length > 0 && (
                <div>
                  <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    People
                  </div>
                  {data.persons.map((person) => (
                    <button
                      key={person.id}
                      onClick={() => handleSelect('person', person.id)}
                      className="w-full flex items-center gap-3 px-3 py-2 hover:bg-accent text-left"
                    >
                      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-semibold">
                        {person.first_name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{person.full_name}</p>
                        {person.nickname && (
                          <p className="text-xs text-muted-foreground truncate">
                            "{person.nickname}"
                          </p>
                        )}
                      </div>
                      <User className="h-4 w-4 text-muted-foreground" />
                    </button>
                  ))}
                </div>
              )}

              {/* Anecdotes Results */}
              {data?.anecdotes && data.anecdotes.length > 0 && (
                <div>
                  {data?.persons && data.persons.length > 0 && (
                    <div className="border-t my-2" />
                  )}
                  <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Anecdotes
                  </div>
                  {data.anecdotes.map((anecdote) => (
                    <button
                      key={anecdote.id}
                      onClick={() => handleSelect('anecdote', anecdote.id)}
                      className="w-full flex items-start gap-3 px-3 py-2 hover:bg-accent text-left"
                    >
                      <BookOpen className="h-4 w-4 text-muted-foreground mt-0.5" />
                      <div className="flex-1 min-w-0">
                        {anecdote.title && (
                          <p className="font-medium text-sm truncate">{anecdote.title}</p>
                        )}
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {anecdote.content}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1 capitalize">
                          {anecdote.anecdote_type}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
