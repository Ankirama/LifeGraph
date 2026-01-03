import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Tag } from 'lucide-react'
import { getTags, createTag } from '@/services/api'
import { Modal } from '@/components/Modal'
import type { Tag as TagType } from '@/types'

const PRESET_COLORS = [
  '#ef4444', // red
  '#f97316', // orange
  '#eab308', // yellow
  '#22c55e', // green
  '#14b8a6', // teal
  '#3b82f6', // blue
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#6b7280', // gray
]

export function TagsPage() {
  const queryClient = useQueryClient()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [editingTag, setEditingTag] = useState<TagType | null>(null)
  const [formData, setFormData] = useState({ name: '', color: PRESET_COLORS[0] })

  const { data: tagsResponse, isLoading } = useQuery({
    queryKey: ['tags'],
    queryFn: getTags,
  })

  const createMutation = useMutation({
    mutationFn: createTag,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      handleCloseModal()
    },
  })

  const handleCloseModal = () => {
    setIsCreateModalOpen(false)
    setEditingTag(null)
    setFormData({ name: '', color: PRESET_COLORS[0] })
  }

  const handleOpenCreate = () => {
    setFormData({ name: '', color: PRESET_COLORS[0] })
    setIsCreateModalOpen(true)
  }

  const handleOpenEdit = (tag: TagType) => {
    setEditingTag(tag)
    setFormData({ name: tag.name, color: tag.color })
    setIsCreateModalOpen(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) return

    createMutation.mutate({
      name: formData.name,
      color: formData.color,
    })
  }

  const tags = tagsResponse?.results || []

  if (isLoading) {
    return <div className="text-muted-foreground">Loading tags...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Tags</h1>
          <p className="text-muted-foreground">
            Organize people with flexible labels
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Create Tag
        </button>
      </div>

      {/* Tags Grid */}
      {tags.length === 0 ? (
        <div className="bg-card border rounded-lg p-12 text-center">
          <Tag className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No tags yet</h3>
          <p className="text-muted-foreground mb-4">
            Create tags to organize and categorize your contacts
          </p>
          <button
            onClick={handleOpenCreate}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Create your first tag
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {tags.map((tag) => (
            <div
              key={tag.id}
              className="bg-card border rounded-lg p-4 hover:shadow-md transition-shadow group"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="h-8 w-8 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: tag.color + '20' }}
                  >
                    <Tag className="h-4 w-4" style={{ color: tag.color }} />
                  </div>
                  <div>
                    <h3 className="font-medium">{tag.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      {tag.person_count || 0} {tag.person_count === 1 ? 'person' : 'people'}
                    </p>
                  </div>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                  <button
                    onClick={() => handleOpenEdit(tag)}
                    className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent rounded"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={handleCloseModal}
        title={editingTag ? 'Edit Tag' : 'Create Tag'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Tag Name <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Family, Work, College Friends"
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Color</label>
            <div className="flex flex-wrap gap-2">
              {PRESET_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setFormData({ ...formData, color })}
                  className={`h-8 w-8 rounded-full transition-transform ${
                    formData.color === color
                      ? 'ring-2 ring-offset-2 ring-primary scale-110'
                      : 'hover:scale-105'
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>

          {/* Preview */}
          <div>
            <label className="block text-sm font-medium mb-2">Preview</label>
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1 text-sm rounded-full"
              style={{ backgroundColor: formData.color + '20', color: formData.color }}
            >
              <Tag className="h-3 w-3" />
              {formData.name || 'Tag name'}
            </span>
          </div>

          {createMutation.error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
              Failed to {editingTag ? 'update' : 'create'} tag. Please try again.
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleCloseModal}
              className="px-4 py-2 text-sm font-medium border rounded-md hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || !formData.name.trim()}
              className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {createMutation.isPending
                ? 'Saving...'
                : editingTag
                  ? 'Update Tag'
                  : 'Create Tag'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
