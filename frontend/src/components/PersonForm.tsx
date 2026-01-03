import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'
import { createPerson, updatePerson, getTags, getGroups } from '@/services/api'
import type { Person, ContactInfo } from '@/types'

interface PersonFormProps {
  person?: Person
  onSuccess: () => void
  onCancel: () => void
}

interface FormData {
  first_name: string
  last_name: string
  nickname: string
  birthday: string
  met_date: string
  met_context: string
  emails: ContactInfo[]
  phones: ContactInfo[]
  addresses: ContactInfo[]
  linkedin_url: string
  discord_id: string
  notes: string
  tag_ids: string[]
  group_ids: string[]
}

export function PersonForm({ person, onSuccess, onCancel }: PersonFormProps) {
  const queryClient = useQueryClient()
  const isEditing = !!person

  const [formData, setFormData] = useState<FormData>({
    first_name: person?.first_name || '',
    last_name: person?.last_name || '',
    nickname: person?.nickname || '',
    birthday: person?.birthday || '',
    met_date: person?.met_date || '',
    met_context: person?.met_context || '',
    emails: person?.emails || [{ email: '', label: 'personal' }],
    phones: person?.phones || [],
    addresses: person?.addresses || [],
    linkedin_url: person?.linkedin_url || '',
    discord_id: person?.discord_id || '',
    notes: person?.notes || '',
    tag_ids: person?.tags?.map((t) => t.id) || [],
    group_ids: person?.groups?.map((g) => g.id) || [],
  })

  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: getTags,
  })

  const { data: groupsData } = useQuery({
    queryKey: ['groups'],
    queryFn: getGroups,
  })

  const createMutation = useMutation({
    mutationFn: createPerson,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      onSuccess()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Person>) => updatePerson(person!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      queryClient.invalidateQueries({ queryKey: ['person', person!.id] })
      onSuccess()
    },
  })

  const isLoading = createMutation.isPending || updateMutation.isPending

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Filter out empty emails/phones/addresses
    const cleanedData = {
      ...formData,
      emails: formData.emails.filter((e) => e.email?.trim()),
      phones: formData.phones.filter((p) => p.phone?.trim()),
      addresses: formData.addresses.filter((a) => a.address?.trim()),
      birthday: formData.birthday || null,
      met_date: formData.met_date || null,
    }

    if (isEditing) {
      updateMutation.mutate(cleanedData)
    } else {
      createMutation.mutate(cleanedData)
    }
  }

  const addContactField = (type: 'emails' | 'phones' | 'addresses') => {
    const newItem =
      type === 'emails'
        ? { email: '', label: 'personal' }
        : type === 'phones'
          ? { phone: '', label: 'mobile' }
          : { address: '', label: 'home' }

    setFormData((prev) => ({
      ...prev,
      [type]: [...prev[type], newItem],
    }))
  }

  const removeContactField = (type: 'emails' | 'phones' | 'addresses', index: number) => {
    setFormData((prev) => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index),
    }))
  }

  const updateContactField = (
    type: 'emails' | 'phones' | 'addresses',
    index: number,
    field: string,
    value: string
  ) => {
    setFormData((prev) => ({
      ...prev,
      [type]: prev[type].map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      ),
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Info */}
      <div className="space-y-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
          Basic Information
        </h3>

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
              placeholder="First name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Last Name</label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData((prev) => ({ ...prev, last_name: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Last name"
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

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Birthday</label>
            <input
              type="date"
              value={formData.birthday}
              onChange={(e) => setFormData((prev) => ({ ...prev, birthday: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Met Date</label>
            <input
              type="date"
              value={formData.met_date}
              onChange={(e) => setFormData((prev) => ({ ...prev, met_date: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">How/Where You Met</label>
          <input
            type="text"
            value={formData.met_context}
            onChange={(e) => setFormData((prev) => ({ ...prev, met_context: e.target.value }))}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="e.g., College roommate, Work conference 2023"
          />
        </div>
      </div>

      {/* Contact Information */}
      <div className="space-y-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
          Contact Information
        </h3>

        {/* Emails */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium">Emails</label>
            <button
              type="button"
              onClick={() => addContactField('emails')}
              className="text-sm text-primary hover:underline inline-flex items-center gap-1"
            >
              <Plus className="h-3 w-3" /> Add
            </button>
          </div>
          <div className="space-y-2">
            {formData.emails.map((email, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="email"
                  value={email.email || ''}
                  onChange={(e) => updateContactField('emails', index, 'email', e.target.value)}
                  className="flex-1 px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="email@example.com"
                />
                <select
                  value={email.label}
                  onChange={(e) => updateContactField('emails', index, 'label', e.target.value)}
                  className="px-3 py-2 rounded-md border bg-background text-sm"
                >
                  <option value="personal">Personal</option>
                  <option value="work">Work</option>
                  <option value="other">Other</option>
                </select>
                <button
                  type="button"
                  onClick={() => removeContactField('emails', index)}
                  className="p-2 text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Phones */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium">Phones</label>
            <button
              type="button"
              onClick={() => addContactField('phones')}
              className="text-sm text-primary hover:underline inline-flex items-center gap-1"
            >
              <Plus className="h-3 w-3" /> Add
            </button>
          </div>
          <div className="space-y-2">
            {formData.phones.map((phone, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="tel"
                  value={phone.phone || ''}
                  onChange={(e) => updateContactField('phones', index, 'phone', e.target.value)}
                  className="flex-1 px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="+1 234 567 8900"
                />
                <select
                  value={phone.label}
                  onChange={(e) => updateContactField('phones', index, 'label', e.target.value)}
                  className="px-3 py-2 rounded-md border bg-background text-sm"
                >
                  <option value="mobile">Mobile</option>
                  <option value="home">Home</option>
                  <option value="work">Work</option>
                </select>
                <button
                  type="button"
                  onClick={() => removeContactField('phones', index)}
                  className="p-2 text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Social Links */}
      <div className="space-y-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
          Social Links
        </h3>

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
      </div>

      {/* Tags & Groups */}
      <div className="space-y-4">
        <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
          Organization
        </h3>

        <div>
          <label className="block text-sm font-medium mb-2">Tags</label>
          <div className="flex flex-wrap gap-2">
            {tagsData?.results.map((tag) => (
              <label
                key={tag.id}
                className={`px-3 py-1 rounded-full text-sm cursor-pointer transition-colors ${
                  formData.tag_ids.includes(tag.id)
                    ? 'ring-2 ring-primary'
                    : 'opacity-60 hover:opacity-100'
                }`}
                style={{ backgroundColor: tag.color + '30', color: tag.color }}
              >
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={formData.tag_ids.includes(tag.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFormData((prev) => ({
                        ...prev,
                        tag_ids: [...prev.tag_ids, tag.id],
                      }))
                    } else {
                      setFormData((prev) => ({
                        ...prev,
                        tag_ids: prev.tag_ids.filter((id) => id !== tag.id),
                      }))
                    }
                  }}
                />
                {tag.name}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Groups</label>
          <div className="flex flex-wrap gap-2">
            {groupsData?.results.map((group) => (
              <label
                key={group.id}
                className={`px-3 py-1 rounded-md text-sm cursor-pointer border transition-colors ${
                  formData.group_ids.includes(group.id)
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={formData.group_ids.includes(group.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFormData((prev) => ({
                        ...prev,
                        group_ids: [...prev.group_ids, group.id],
                      }))
                    } else {
                      setFormData((prev) => ({
                        ...prev,
                        group_ids: prev.group_ids.filter((id) => id !== group.id),
                      }))
                    }
                  }}
                />
                {group.name}
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium mb-1">Notes</label>
        <textarea
          value={formData.notes}
          onChange={(e) => setFormData((prev) => ({ ...prev, notes: e.target.value }))}
          className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[100px]"
          placeholder="General notes about this person..."
        />
      </div>

      {/* Error Display */}
      {(createMutation.error || updateMutation.error) && (
        <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
          Failed to save person. Please try again.
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium border rounded-md hover:bg-accent"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading || !formData.first_name.trim()}
          className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {isLoading ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Person'}
        </button>
      </div>
    </form>
  )
}
