import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Search, Heart, Sparkles, RefreshCw } from 'lucide-react'
import { getPersons } from '@/services/api'
import { Modal } from '@/components/Modal'
import { PersonForm } from '@/components/PersonForm'
import { AIImportModal } from '@/components/AIImportModal'
import { AIUpdateModal } from '@/components/AIUpdateModal'

export function PeopleList() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isAIImportOpen, setIsAIImportOpen] = useState(false)
  const [isAIUpdateOpen, setIsAIUpdateOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['persons', { search: searchQuery }],
    queryFn: () => getPersons({ search: searchQuery }),
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
        <div className="flex gap-2">
          <button
            onClick={() => setIsAIUpdateOpen(true)}
            className="inline-flex items-center gap-2 border px-4 py-2 rounded-md text-sm font-medium hover:bg-accent"
          >
            <RefreshCw className="h-4 w-4" />
            AI Update
          </button>
          <button
            onClick={() => setIsAIImportOpen(true)}
            className="inline-flex items-center gap-2 border px-4 py-2 rounded-md text-sm font-medium hover:bg-accent"
          >
            <Sparkles className="h-4 w-4" />
            AI Import
          </button>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Add Person
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
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
          <h3 className="text-lg font-semibold mb-2">
            {searchQuery ? 'No results found' : 'No people yet'}
          </h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery
              ? `No people match "${searchQuery}"`
              : 'Start building your personal CRM by adding your first contact.'}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-primary/90"
            >
              <Plus className="h-4 w-4" />
              Add Your First Person
            </button>
          )}
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
                  {person.first_name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold truncate">{person.full_name}</h3>
                    {person.relationship_to_me && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300 whitespace-nowrap">
                        <Heart className="h-3 w-3" />
                        {person.relationship_to_me}
                      </span>
                    )}
                  </div>
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

      {/* Add Person Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Person"
        size="xl"
      >
        <PersonForm
          onSuccess={() => setIsAddModalOpen(false)}
          onCancel={() => setIsAddModalOpen(false)}
        />
      </Modal>

      {/* AI Import Modal */}
      <AIImportModal
        isOpen={isAIImportOpen}
        onClose={() => setIsAIImportOpen(false)}
      />

      {/* AI Update Modal */}
      <AIUpdateModal
        isOpen={isAIUpdateOpen}
        onClose={() => setIsAIUpdateOpen(false)}
      />
    </div>
  )
}
