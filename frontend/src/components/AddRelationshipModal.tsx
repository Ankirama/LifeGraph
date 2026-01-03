import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { User } from 'lucide-react'
import { Modal } from './Modal'
import { createRelationship, getPersons, getRelationshipTypes, getMe } from '@/services/api'

interface AddRelationshipModalProps {
  isOpen: boolean
  onClose: () => void
  personId: string
  personName: string
}

export function AddRelationshipModal({
  isOpen,
  onClose,
  personId,
  personName,
}: AddRelationshipModalProps) {
  const queryClient = useQueryClient()
  const [selectedPerson, setSelectedPerson] = useState('')
  const [selectedType, setSelectedType] = useState('')
  const [notes, setNotes] = useState('')
  const [strength, setStrength] = useState<number | ''>('')
  const [startedDate, setStartedDate] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const { data: persons } = useQuery({
    queryKey: ['persons', { search: searchQuery }],
    queryFn: () => getPersons({ search: searchQuery }),
    enabled: isOpen,
  })

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    enabled: isOpen,
    retry: false, // Don't retry if Me doesn't exist (404)
  })

  const { data: relationshipTypes } = useQuery({
    queryKey: ['relationshipTypes'],
    queryFn: getRelationshipTypes,
    enabled: isOpen,
  })

  const mutation = useMutation({
    mutationFn: createRelationship,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['person', personId, 'relationships'] })
      handleClose()
    },
  })

  const handleClose = () => {
    setSelectedPerson('')
    setSelectedType('')
    setNotes('')
    setStrength('')
    setStartedDate('')
    setSearchQuery('')
    onClose()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedPerson || !selectedType) return

    mutation.mutate({
      person_a: personId,
      person_b: selectedPerson,
      relationship_type: selectedType,
      notes,
      strength: strength || null,
      started_date: startedDate || null,
    })
  }

  // Filter out the current person from the list
  const availablePersons = persons?.results.filter((p) => p.id !== personId) || []

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add Relationship" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Add a relationship for <span className="font-medium text-foreground">{personName}</span>
        </p>

        {/* Person Search */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Related Person <span className="text-destructive">*</span>
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring mb-2"
            placeholder="Search by name..."
          />
          <div className="max-h-40 overflow-y-auto border rounded-md">
            {/* Me option - always shown first if exists and not the current person */}
            {me && me.id !== personId && (
              <button
                type="button"
                onClick={() => setSelectedPerson(me.id)}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-accent flex items-center gap-3 border-b ${
                  selectedPerson === me.id ? 'bg-accent' : ''
                }`}
              >
                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-semibold">
                  <User className="h-4 w-4" />
                </div>
                <div>
                  <p className="font-medium">{me.full_name} <span className="text-xs text-primary">(Me)</span></p>
                </div>
              </button>
            )}
            {availablePersons.length === 0 && !me ? (
              <p className="p-3 text-sm text-muted-foreground">No people found</p>
            ) : (
              availablePersons.map((person) => (
                <button
                  key={person.id}
                  type="button"
                  onClick={() => setSelectedPerson(person.id)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-accent flex items-center gap-3 ${
                    selectedPerson === person.id ? 'bg-accent' : ''
                  }`}
                >
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-semibold">
                    {person.first_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="font-medium">{person.full_name}</p>
                    {person.nickname && (
                      <p className="text-xs text-muted-foreground">"{person.nickname}"</p>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Relationship Type */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Relationship Type <span className="text-destructive">*</span>
          </label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            required
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">Select type...</option>
            {relationshipTypes?.results.map((type) => (
              <option key={type.id} value={type.id}>
                {type.name}
                {type.inverse_name && type.inverse_name !== type.name
                  ? ` / ${type.inverse_name}`
                  : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Strength */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Relationship Strength (1-5)
          </label>
          <input
            type="number"
            min="1"
            max="5"
            value={strength}
            onChange={(e) => setStrength(e.target.value ? parseInt(e.target.value) : '')}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Optional (1 = weak, 5 = strong)"
          />
        </div>

        {/* Started Date */}
        <div>
          <label className="block text-sm font-medium mb-1">Started Date</label>
          <input
            type="date"
            value={startedDate}
            onChange={(e) => setStartedDate(e.target.value)}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium mb-1">Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
            placeholder="How do they know each other?"
          />
        </div>

        {/* Error */}
        {mutation.error && (
          <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
            Failed to create relationship. It may already exist.
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium border rounded-md hover:bg-accent"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending || !selectedPerson || !selectedType}
            className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {mutation.isPending ? 'Adding...' : 'Add Relationship'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
