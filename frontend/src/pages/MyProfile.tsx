import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { UserCircle, Save } from 'lucide-react'
import { getMe, createMe, updateMe } from '@/services/api'
import type { Person } from '@/types'

export function MyProfile() {
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)

  const { data: me, isLoading, error } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    retry: false,
  })

  const needsSetup = error && (error as { response?: { status?: number } })?.response?.status === 404

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    nickname: '',
    birthday: '',
    linkedin_url: '',
    discord_id: '',
    notes: '',
  })

  // Update form when me data loads
  useEffect(() => {
    if (me) {
      setFormData({
        first_name: me.first_name || '',
        last_name: me.last_name || '',
        nickname: me.nickname || '',
        birthday: me.birthday || '',
        linkedin_url: me.linkedin_url || '',
        discord_id: me.discord_id || '',
        notes: me.notes || '',
      })
    }
  }, [me])

  const createMutation = useMutation({
    mutationFn: createMe,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
      setIsEditing(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: updateMe,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
      setIsEditing(false)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data = {
      ...formData,
      birthday: formData.birthday || null,
    }
    if (needsSetup) {
      createMutation.mutate(data as Partial<Person>)
    } else {
      updateMutation.mutate(data as Partial<Person>)
    }
  }

  const isSubmitting = createMutation.isPending || updateMutation.isPending

  if (isLoading) {
    return <div className="text-muted-foreground">Loading...</div>
  }

  // Setup mode or editing mode
  if (needsSetup || isEditing) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
            <UserCircle className="h-10 w-10 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">
              {needsSetup ? 'Set Up Your Profile' : 'Edit Your Profile'}
            </h2>
            <p className="text-muted-foreground">
              {needsSetup
                ? 'Create your profile to start tracking relationships'
                : 'Update your personal information'}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-card border rounded-lg p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                First Name <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.first_name}
                onChange={(e) => setFormData((prev) => ({ ...prev, first_name: e.target.value }))}
                className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Your first name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Last Name</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData((prev) => ({ ...prev, last_name: e.target.value }))}
                className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Your last name"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Nickname</label>
            <input
              type="text"
              value={formData.nickname}
              onChange={(e) => setFormData((prev) => ({ ...prev, nickname: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Optional nickname"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Birthday</label>
            <input
              type="date"
              value={formData.birthday}
              onChange={(e) => setFormData((prev) => ({ ...prev, birthday: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">LinkedIn URL</label>
              <input
                type="url"
                value={formData.linkedin_url}
                onChange={(e) => setFormData((prev) => ({ ...prev, linkedin_url: e.target.value }))}
                className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="https://linkedin.com/in/..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Discord ID</label>
              <input
                type="text"
                value={formData.discord_id}
                onChange={(e) => setFormData((prev) => ({ ...prev, discord_id: e.target.value }))}
                className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="username#1234"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">About Me</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData((prev) => ({ ...prev, notes: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[100px]"
              placeholder="A brief description about yourself..."
            />
          </div>

          {(createMutation.error || updateMutation.error) && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
              Failed to save profile. Please try again.
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t">
            {!needsSetup && (
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 text-sm font-medium border rounded-md hover:bg-accent"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={isSubmitting || !formData.first_name.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {isSubmitting ? 'Saving...' : needsSetup ? 'Create Profile' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    )
  }

  // View mode
  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-2xl font-semibold">
            {me?.first_name?.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-2xl font-bold">{me?.full_name}</h2>
            {me?.nickname && (
              <p className="text-muted-foreground">"{me.nickname}"</p>
            )}
          </div>
        </div>
        <button
          onClick={() => {
            setFormData({
              first_name: me?.first_name || '',
              last_name: me?.last_name || '',
              nickname: me?.nickname || '',
              birthday: me?.birthday || '',
              linkedin_url: me?.linkedin_url || '',
              discord_id: me?.discord_id || '',
              notes: me?.notes || '',
            })
            setIsEditing(true)
          }}
          className="px-4 py-2 text-sm font-medium border rounded-md hover:bg-accent"
        >
          Edit Profile
        </button>
      </div>

      <div className="bg-card border rounded-lg p-6 space-y-6">
        {me?.birthday && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1">Birthday</h3>
            <p>{new Date(me.birthday).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
          </div>
        )}

        {(me?.linkedin_url || me?.discord_id) && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Social Links</h3>
            <div className="space-y-1">
              {me?.linkedin_url && (
                <a
                  href={me.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline block"
                >
                  LinkedIn Profile
                </a>
              )}
              {me?.discord_id && (
                <p>Discord: {me.discord_id}</p>
              )}
            </div>
          </div>
        )}

        {me?.notes && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1">About</h3>
            <p className="whitespace-pre-wrap">{me.notes}</p>
          </div>
        )}

        <div className="pt-4 border-t text-sm text-muted-foreground">
          <p>This is your profile in the CRM. When you create relationships, you can link people to yourself.</p>
        </div>
      </div>
    </div>
  )
}
