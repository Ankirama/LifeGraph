import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Modal } from './Modal'
import { createAnecdote, getTags } from '@/services/api'
import type { Anecdote } from '@/types'

interface AddAnecdoteModalProps {
  isOpen: boolean
  onClose: () => void
  personId: string
  personName: string
}

type AnecdoteType = Anecdote['anecdote_type']

export function AddAnecdoteModal({
  isOpen,
  onClose,
  personId,
  personName,
}: AddAnecdoteModalProps) {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [anecdoteType, setAnecdoteType] = useState<AnecdoteType>('note')
  const [date, setDate] = useState('')
  const [location, setLocation] = useState('')
  const [tagIds, setTagIds] = useState<string[]>([])

  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: getTags,
    enabled: isOpen,
  })

  const mutation = useMutation({
    mutationFn: createAnecdote,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['person', personId, 'anecdotes'] })
      handleClose()
    },
  })

  const handleClose = () => {
    setTitle('')
    setContent('')
    setAnecdoteType('note')
    setDate('')
    setLocation('')
    setTagIds([])
    onClose()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) return

    mutation.mutate({
      title,
      content,
      anecdote_type: anecdoteType,
      date: date || null,
      location,
      person_ids: [personId],
      tag_ids: tagIds,
    })
  }

  const anecdoteTypes: { value: AnecdoteType; label: string; description: string }[] = [
    { value: 'note', label: 'Note', description: 'General notes and observations' },
    { value: 'memory', label: 'Memory', description: 'Shared experiences and moments' },
    { value: 'quote', label: 'Quote', description: 'Something memorable they said' },
    { value: 'joke', label: 'Joke', description: 'Funny moments or inside jokes' },
  ]

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add Anecdote" size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Add a memory, note, or quote about{' '}
          <span className="font-medium text-foreground">{personName}</span>
        </p>

        {/* Anecdote Type */}
        <div>
          <label className="block text-sm font-medium mb-2">Type</label>
          <div className="grid grid-cols-4 gap-2">
            {anecdoteTypes.map((type) => (
              <button
                key={type.value}
                type="button"
                onClick={() => setAnecdoteType(type.value)}
                className={`p-3 text-left border rounded-md transition-colors ${
                  anecdoteType === type.value
                    ? 'border-primary bg-primary/5'
                    : 'hover:border-primary/50'
                }`}
              >
                <p className="font-medium text-sm">{type.label}</p>
                <p className="text-xs text-muted-foreground">{type.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Title */}
        <div>
          <label className="block text-sm font-medium mb-1">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Optional title for this anecdote"
          />
        </div>

        {/* Content */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Content <span className="text-destructive">*</span>
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[150px]"
            placeholder={
              anecdoteType === 'quote'
                ? '"Enter the quote here..."'
                : anecdoteType === 'memory'
                  ? 'Describe the memory or experience...'
                  : anecdoteType === 'joke'
                    ? 'What was the funny moment?'
                    : 'Write your notes here...'
            }
          />
        </div>

        {/* Date and Location */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Where did this happen?"
            />
          </div>
        </div>

        {/* Tags */}
        {tagsData && tagsData.results.length > 0 && (
          <div>
            <label className="block text-sm font-medium mb-2">Tags</label>
            <div className="flex flex-wrap gap-2">
              {tagsData.results.map((tag) => (
                <label
                  key={tag.id}
                  className={`px-3 py-1 rounded-full text-sm cursor-pointer transition-colors ${
                    tagIds.includes(tag.id)
                      ? 'ring-2 ring-primary'
                      : 'opacity-60 hover:opacity-100'
                  }`}
                  style={{ backgroundColor: tag.color + '30', color: tag.color }}
                >
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={tagIds.includes(tag.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setTagIds((prev) => [...prev, tag.id])
                      } else {
                        setTagIds((prev) => prev.filter((id) => id !== tag.id))
                      }
                    }}
                  />
                  {tag.name}
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {mutation.error && (
          <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
            Failed to create anecdote. Please try again.
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
            disabled={mutation.isPending || !content.trim()}
            className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {mutation.isPending ? 'Adding...' : 'Add Anecdote'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
