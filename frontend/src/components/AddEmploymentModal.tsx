import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from './Modal'
import { createEmployment } from '@/services/api'

interface AddEmploymentModalProps {
  isOpen: boolean
  onClose: () => void
  personId: string
  personName: string
}

export function AddEmploymentModal({
  isOpen,
  onClose,
  personId,
  personName,
}: AddEmploymentModalProps) {
  const queryClient = useQueryClient()
  const [company, setCompany] = useState('')
  const [title, setTitle] = useState('')
  const [department, setDepartment] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [isCurrent, setIsCurrent] = useState(false)
  const [location, setLocation] = useState('')
  const [description, setDescription] = useState('')

  const mutation = useMutation({
    mutationFn: createEmployment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['person', personId, 'employments'] })
      handleClose()
    },
  })

  const handleClose = () => {
    setCompany('')
    setTitle('')
    setDepartment('')
    setStartDate('')
    setEndDate('')
    setIsCurrent(false)
    setLocation('')
    setDescription('')
    onClose()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!company.trim() || !title.trim()) return

    mutation.mutate({
      person: personId,
      company,
      title,
      department,
      start_date: startDate || null,
      end_date: isCurrent ? null : endDate || null,
      is_current: isCurrent,
      location,
      description,
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add Employment" size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Add employment history for{' '}
          <span className="font-medium text-foreground">{personName}</span>
        </p>

        {/* Company and Title */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Company <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Company name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Job Title <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Job title"
            />
          </div>
        </div>

        {/* Department */}
        <div>
          <label className="block text-sm font-medium mb-1">Department</label>
          <input
            type="text"
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="e.g., Engineering, Sales, Marketing"
          />
        </div>

        {/* Current Job Checkbox */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_current"
            checked={isCurrent}
            onChange={(e) => {
              setIsCurrent(e.target.checked)
              if (e.target.checked) {
                setEndDate('')
              }
            }}
            className="rounded"
          />
          <label htmlFor="is_current" className="text-sm font-medium">
            This is a current position
          </label>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              disabled={isCurrent}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
        </div>

        {/* Location */}
        <div>
          <label className="block text-sm font-medium mb-1">Location</label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="e.g., San Francisco, CA or Remote"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
            placeholder="Brief description of responsibilities or achievements..."
          />
        </div>

        {/* Error */}
        {mutation.error && (
          <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
            Failed to add employment. Please try again.
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
            disabled={mutation.isPending || !company.trim() || !title.trim()}
            className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {mutation.isPending ? 'Adding...' : 'Add Employment'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
