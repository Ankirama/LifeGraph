import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Search } from 'lucide-react'
import { getPersons } from '@/services/api'

export function PeopleList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['persons'],
    queryFn: () => getPersons(),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">People</h2>
          <p className="text-muted-foreground">
            Manage your contacts and relationships
          </p>
        </div>
        <button className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90">
          <Plus className="h-4 w-4" />
          Add Person
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by name..."
            className="w-full pl-10 pr-4 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {/* People List */}
      {isLoading ? (
        <div className="text-muted-foreground">Loading...</div>
      ) : error ? (
        <div className="text-destructive">
          Error loading people. Make sure the backend is running.
        </div>
      ) : data?.results.length === 0 ? (
        <div className="bg-card border rounded-lg p-12 text-center">
          <h3 className="text-lg font-semibold mb-2">No people yet</h3>
          <p className="text-muted-foreground mb-4">
            Start building your personal CRM by adding your first contact.
          </p>
          <button className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90">
            <Plus className="h-4 w-4" />
            Add Your First Person
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.results.map((person) => (
            <Link
              key={person.id}
              to={`/people/${person.id}`}
              className="bg-card border rounded-lg p-4 hover:border-primary transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold">
                  {person.name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold truncate">{person.name}</h3>
                  {person.nickname && (
                    <p className="text-sm text-muted-foreground truncate">
                      "{person.nickname}"
                    </p>
                  )}
                </div>
              </div>
              {person.tags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {person.tags.slice(0, 3).map((tag) => (
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
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
