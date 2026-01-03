import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Modal } from './Modal'
import { updateRelationship, getRelationshipTypes } from '@/services/api'
import type { Relationship } from '@/types'

interface EditRelationshipModalProps {
  isOpen: boolean
  onClose: () => void
  relationship: Relationship
  currentPersonId: string
}

export function EditRelationshipModal({
  isOpen,
  onClose,
  relationship,
  currentPersonId,
}: EditRelationshipModalProps) {
  const queryClient = useQueryClient()
  const [selectedType, setSelectedType] = useState('')
  const [notes, setNotes] = useState('')
  const [strength, setStrength] = useState<number | ''>('')
  const [startedDate, setStartedDate] = useState('')

  // Get the other person's name for display
  const otherPersonName =
    relationship.person_a === currentPersonId
      ? relationship.person_b_name
      : relationship.person_a_name

  // Initialize form with existing data
  useEffect(() => {
    if (relationship) {
      setSelectedType(relationship.relationship_type)
      setNotes(relationship.notes || '')
      setStrength(relationship.strength || '')
      setStartedDate(relationship.started_date || '')
    }
  }, [relationship])

  const { data: relationshipTypes } = useQuery({
    queryKey: ['relationshipTypes'],
    queryFn: getRelationshipTypes,
    enabled: isOpen,
  })

  const mutation = useMutation({
    mutationFn: (data: Partial<Relationship>) =>
      updateRelationship(relationship.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['person', currentPersonId, 'relationships'],
      })
      queryClient.invalidateQueries({ queryKey: ['relationships'] })
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      handleClose()
    },
  })

  const handleClose = () => {
    onClose()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedType) return

    mutation.mutate({
      relationship_type: selectedType,
      notes,
      strength: strength || null,
      started_date: startedDate || null,
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Edit Relationship" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Edit relationship with{' '}
          <span className="font-medium text-foreground">{otherPersonName}</span>
        </p>

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
          <p className="text-xs text-muted-foreground mt-1">
            The first term describes what {otherPersonName} is to you
          </p>
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
            onChange={(e) =>
              setStrength(e.target.value ? parseInt(e.target.value) : '')
            }
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
            Failed to update relationship. Please try again.
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
            disabled={mutation.isPending || !selectedType}
            className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {mutation.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
