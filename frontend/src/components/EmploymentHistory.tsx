import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Briefcase, Building2, MapPin, Trash2, Linkedin } from 'lucide-react'
import { deleteEmployment } from '@/services/api'
import { format } from 'date-fns'
import type { Employment } from '@/types'

interface EmploymentHistoryProps {
  employments: Employment[]
  personId: string
}

export function EmploymentHistory({ employments, personId }: EmploymentHistoryProps) {
  const queryClient = useQueryClient()

  const deleteMutation = useMutation({
    mutationFn: deleteEmployment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['person', personId, 'employments'] })
    },
  })

  if (employments.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No employment history yet.
      </p>
    )
  }

  // Sort by start date, current jobs first
  const sortedEmployments = [...employments].sort((a, b) => {
    if (a.is_current && !b.is_current) return -1
    if (!a.is_current && b.is_current) return 1
    if (!a.start_date && !b.start_date) return 0
    if (!a.start_date) return 1
    if (!b.start_date) return -1
    return new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
  })

  return (
    <div className="space-y-4">
      {sortedEmployments.map((employment) => (
        <div
          key={employment.id}
          className="relative pl-6 pb-4 border-l-2 border-border last:pb-0"
        >
          {/* Timeline dot */}
          <div
            className={`absolute left-[-5px] top-1 h-2 w-2 rounded-full ${
              employment.is_current ? 'bg-green-500' : 'bg-muted-foreground'
            }`}
          />

          <div className="group">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {/* Title and Company */}
                <div className="flex items-center gap-2">
                  <h4 className="font-medium">{employment.title}</h4>
                  {employment.is_current && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full dark:bg-green-900 dark:text-green-300">
                      Current
                    </span>
                  )}
                  {employment.linkedin_synced && (
                    <Linkedin className="h-3 w-3 text-blue-600" />
                  )}
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground mt-0.5">
                  <Building2 className="h-3.5 w-3.5" />
                  <span>{employment.company}</span>
                  {employment.department && (
                    <>
                      <span>·</span>
                      <span>{employment.department}</span>
                    </>
                  )}
                </div>

                {/* Date Range */}
                <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                  <Briefcase className="h-3.5 w-3.5" />
                  <span>
                    {employment.start_date
                      ? format(new Date(employment.start_date), 'MMM yyyy')
                      : 'Unknown'}
                    {' — '}
                    {employment.is_current
                      ? 'Present'
                      : employment.end_date
                        ? format(new Date(employment.end_date), 'MMM yyyy')
                        : 'Unknown'}
                  </span>
                  {employment.start_date && (
                    <span className="text-xs">
                      (
                      {calculateDuration(
                        employment.start_date,
                        employment.end_date || new Date().toISOString()
                      )}
                      )
                    </span>
                  )}
                </div>

                {/* Location */}
                {employment.location && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                    <MapPin className="h-3.5 w-3.5" />
                    <span>{employment.location}</span>
                  </div>
                )}

                {/* Description */}
                {employment.description && (
                  <p className="text-sm mt-2 text-muted-foreground">
                    {employment.description}
                  </p>
                )}
              </div>

              {/* Delete button */}
              <button
                onClick={() => {
                  if (confirm('Are you sure you want to delete this employment record?')) {
                    deleteMutation.mutate(employment.id)
                  }
                }}
                disabled={deleteMutation.isPending}
                className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-opacity"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function calculateDuration(startDate: string, endDate: string): string {
  const start = new Date(startDate)
  const end = new Date(endDate)

  const months =
    (end.getFullYear() - start.getFullYear()) * 12 +
    (end.getMonth() - start.getMonth())

  if (months < 12) {
    return `${months} mo${months !== 1 ? 's' : ''}`
  }

  const years = Math.floor(months / 12)
  const remainingMonths = months % 12

  if (remainingMonths === 0) {
    return `${years} yr${years !== 1 ? 's' : ''}`
  }

  return `${years} yr${years !== 1 ? 's' : ''} ${remainingMonths} mo${remainingMonths !== 1 ? 's' : ''}`
}
