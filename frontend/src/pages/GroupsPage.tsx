import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, FolderTree, ChevronRight, Users } from 'lucide-react'
import { getGroups, createGroup } from '@/services/api'
import { Modal } from '@/components/Modal'
import type { Group } from '@/types'

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

interface GroupFormData {
  name: string
  description: string
  color: string
  parent: string | null
}

export function GroupsPage() {
  const queryClient = useQueryClient()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<Group | null>(null)
  const [formData, setFormData] = useState<GroupFormData>({
    name: '',
    description: '',
    color: PRESET_COLORS[0],
    parent: null,
  })

  const { data: groupsResponse, isLoading } = useQuery({
    queryKey: ['groups'],
    queryFn: getGroups,
  })

  const createMutation = useMutation({
    mutationFn: createGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
      handleCloseModal()
    },
  })

  const handleCloseModal = () => {
    setIsCreateModalOpen(false)
    setEditingGroup(null)
    setFormData({ name: '', description: '', color: PRESET_COLORS[0], parent: null })
  }

  const handleOpenCreate = (parentId: string | null = null) => {
    setFormData({ name: '', description: '', color: PRESET_COLORS[0], parent: parentId })
    setIsCreateModalOpen(true)
  }

  const handleOpenEdit = (group: Group) => {
    setEditingGroup(group)
    setFormData({
      name: group.name,
      description: group.description || '',
      color: group.color,
      parent: group.parent,
    })
    setIsCreateModalOpen(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) return

    createMutation.mutate({
      name: formData.name,
      description: formData.description,
      color: formData.color,
      parent: formData.parent,
    })
  }

  const groups = groupsResponse?.results || []

  // Build tree structure
  const rootGroups = groups.filter((g) => !g.parent)
  const getChildren = (parentId: string) => groups.filter((g) => g.parent === parentId)

  if (isLoading) {
    return <div className="text-muted-foreground">Loading groups...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Groups</h1>
          <p className="text-muted-foreground">
            Organize people into hierarchical categories
          </p>
        </div>
        <button
          onClick={() => handleOpenCreate()}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Create Group
        </button>
      </div>

      {/* Groups Tree */}
      {groups.length === 0 ? (
        <div className="bg-card border rounded-lg p-12 text-center">
          <FolderTree className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No groups yet</h3>
          <p className="text-muted-foreground mb-4">
            Create groups to organize your contacts hierarchically
          </p>
          <button
            onClick={() => handleOpenCreate()}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Create your first group
          </button>
        </div>
      ) : (
        <div className="bg-card border rounded-lg divide-y">
          {rootGroups.map((group) => (
            <GroupItem
              key={group.id}
              group={group}
              getChildren={getChildren}
              onEdit={handleOpenEdit}
              onCreateChild={handleOpenCreate}
              level={0}
            />
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={handleCloseModal}
        title={editingGroup ? 'Edit Group' : 'Create Group'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {formData.parent && (
            <div className="p-3 bg-muted rounded-md text-sm">
              Creating subgroup under:{' '}
              <span className="font-medium">
                {groups.find((g) => g.id === formData.parent)?.full_path}
              </span>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">
              Group Name <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Work, Family, School"
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Optional description..."
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
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

          {!editingGroup && !formData.parent && groups.length > 0 && (
            <div>
              <label className="block text-sm font-medium mb-1">
                Parent Group (optional)
              </label>
              <select
                value={formData.parent || ''}
                onChange={(e) =>
                  setFormData({ ...formData, parent: e.target.value || null })
                }
                className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">No parent (top-level group)</option>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.full_path}
                  </option>
                ))}
              </select>
            </div>
          )}

          {createMutation.error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
              Failed to {editingGroup ? 'update' : 'create'} group. Please try again.
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
                : editingGroup
                  ? 'Update Group'
                  : 'Create Group'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

interface GroupItemProps {
  group: Group
  getChildren: (parentId: string) => Group[]
  onEdit: (group: Group) => void
  onCreateChild: (parentId: string) => void
  level: number
}

function GroupItem({ group, getChildren, onEdit, onCreateChild, level }: GroupItemProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const children = getChildren(group.id)
  const hasChildren = children.length > 0

  return (
    <div>
      <div
        className="flex items-center gap-3 p-4 hover:bg-accent/50 transition-colors group"
        style={{ paddingLeft: `${level * 24 + 16}px` }}
      >
        {/* Expand/collapse button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`p-1 rounded hover:bg-accent transition-transform ${
            hasChildren ? '' : 'invisible'
          } ${isExpanded ? 'rotate-90' : ''}`}
        >
          <ChevronRight className="h-4 w-4" />
        </button>

        {/* Group icon */}
        <div
          className="h-8 w-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: group.color + '20' }}
        >
          <FolderTree className="h-4 w-4" style={{ color: group.color }} />
        </div>

        {/* Group info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium truncate">{group.name}</h3>
            {group.children_count > 0 && (
              <span className="text-xs text-muted-foreground">
                ({group.children_count} subgroup{group.children_count !== 1 ? 's' : ''})
              </span>
            )}
          </div>
          {group.description && (
            <p className="text-sm text-muted-foreground truncate">{group.description}</p>
          )}
        </div>

        {/* Member count */}
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          <span>0</span>
        </div>

        {/* Actions */}
        <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
          <button
            onClick={() => onCreateChild(group.id)}
            className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent rounded"
            title="Add subgroup"
          >
            <Plus className="h-4 w-4" />
          </button>
          <button
            onClick={() => onEdit(group)}
            className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent rounded"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {children.map((child) => (
            <GroupItem
              key={child.id}
              group={child}
              getChildren={getChildren}
              onEdit={onEdit}
              onCreateChild={onCreateChild}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
