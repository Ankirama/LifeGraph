import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Edit, Calendar, MapPin, Mail, Phone, Plus, Camera, Briefcase, Pencil, Trash2, Sparkles, RefreshCw, Loader2 } from 'lucide-react'
import { getPerson, getPersonRelationships, getPersonAnecdotes, getPersonPhotos, getPersonEmployments, deleteRelationship, generatePersonSummary } from '@/services/api'
import { format } from 'date-fns'
import { Modal } from '@/components/Modal'
import { PersonForm } from '@/components/PersonForm'
import { AddRelationshipModal } from '@/components/AddRelationshipModal'
import { EditRelationshipModal } from '@/components/EditRelationshipModal'
import { AddAnecdoteModal } from '@/components/AddAnecdoteModal'
import { PhotoGallery } from '@/components/PhotoGallery'
import { PhotoUpload } from '@/components/PhotoUpload'
import { EmploymentHistory } from '@/components/EmploymentHistory'
import { AddEmploymentModal } from '@/components/AddEmploymentModal'
import type { Relationship } from '@/types'

export function PersonDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isAddRelationshipOpen, setIsAddRelationshipOpen] = useState(false)
  const [editingRelationship, setEditingRelationship] = useState<Relationship | null>(null)
  const [isAddAnecdoteOpen, setIsAddAnecdoteOpen] = useState(false)
  const [isPhotoUploadOpen, setIsPhotoUploadOpen] = useState(false)
  const [isAddEmploymentOpen, setIsAddEmploymentOpen] = useState(false)

  const deleteRelationshipMutation = useMutation({
    mutationFn: deleteRelationship,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['person', id, 'relationships'] })
      queryClient.invalidateQueries({ queryKey: ['relationships'] })
      queryClient.invalidateQueries({ queryKey: ['persons'] })
    },
  })

  const generateSummaryMutation = useMutation({
    mutationFn: () => generatePersonSummary(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['person', id] })
    },
  })

  const handleDeleteRelationship = (relationshipId: string, otherPersonName: string) => {
    if (confirm(`Remove relationship with ${otherPersonName}?`)) {
      deleteRelationshipMutation.mutate(relationshipId)
    }
  }

  const { data: person, isLoading } = useQuery({
    queryKey: ['person', id],
    queryFn: () => getPerson(id!),
    enabled: !!id,
  })

  const { data: relationships } = useQuery({
    queryKey: ['person', id, 'relationships'],
    queryFn: () => getPersonRelationships(id!),
    enabled: !!id,
  })

  const { data: anecdotes } = useQuery({
    queryKey: ['person', id, 'anecdotes'],
    queryFn: () => getPersonAnecdotes(id!),
    enabled: !!id,
  })

  const { data: photos } = useQuery({
    queryKey: ['person', id, 'photos'],
    queryFn: () => getPersonPhotos(id!),
    enabled: !!id,
  })

  const { data: employments } = useQuery({
    queryKey: ['person', id, 'employments'],
    queryFn: () => getPersonEmployments(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return <div className="text-muted-foreground">Loading...</div>
  }

  if (!person) {
    return <div className="text-destructive">Person not found</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/people"
            className="p-2 hover:bg-accent rounded-md transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary text-2xl font-semibold">
              {person.first_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-2xl font-bold">{person.full_name}</h2>
              {person.nickname && (
                <p className="text-muted-foreground">"{person.nickname}"</p>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={() => setIsEditModalOpen(true)}
          className="inline-flex items-center gap-2 border px-4 py-2 rounded-md text-sm font-medium hover:bg-accent"
        >
          <Edit className="h-4 w-4" />
          Edit
        </button>
      </div>

      {/* Quick Info */}
      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
        {person.birthday && (
          <span className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            {format(new Date(person.birthday), 'MMMM d')}
          </span>
        )}
        {person.met_context && (
          <span className="flex items-center gap-1">
            <MapPin className="h-4 w-4" />
            {person.met_context}
          </span>
        )}
        {person.primary_email && (
          <span className="flex items-center gap-1">
            <Mail className="h-4 w-4" />
            {person.primary_email}
          </span>
        )}
        {person.primary_phone && (
          <span className="flex items-center gap-1">
            <Phone className="h-4 w-4" />
            {person.primary_phone}
          </span>
        )}
      </div>

      {/* Tags */}
      {person.tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {person.tags.map((tag) => (
            <span
              key={tag.id}
              className="px-3 py-1 text-sm rounded-full"
              style={{ backgroundColor: tag.color + '20', color: tag.color }}
            >
              {tag.name}
            </span>
          ))}
        </div>
      )}

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Summary */}
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                AI Summary
              </h3>
              <button
                onClick={() => generateSummaryMutation.mutate()}
                disabled={generateSummaryMutation.isPending}
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generateSummaryMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : person.ai_summary ? (
                  <>
                    <RefreshCw className="h-4 w-4" />
                    Regenerate
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Generate
                  </>
                )}
              </button>
            </div>
            {generateSummaryMutation.isError && (
              <p className="text-sm text-destructive mb-2">
                Failed to generate summary. Please try again.
              </p>
            )}
            {person.ai_summary ? (
              <p className="text-muted-foreground whitespace-pre-wrap">{person.ai_summary}</p>
            ) : (
              <p className="text-muted-foreground text-sm italic">
                No AI summary yet. Click "Generate" to create one based on this person's profile, relationships, and anecdotes.
              </p>
            )}
          </div>

          {/* Notes */}
          {person.notes && (
            <div className="bg-card border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Notes</h3>
              <p className="whitespace-pre-wrap">{person.notes}</p>
            </div>
          )}

          {/* Anecdotes */}
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Anecdotes</h3>
              <button
                onClick={() => setIsAddAnecdoteOpen(true)}
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
              >
                <Plus className="h-4 w-4" />
                Add
              </button>
            </div>
            {anecdotes && anecdotes.length > 0 ? (
              <div className="space-y-4">
                {anecdotes.map((anecdote) => (
                  <div key={anecdote.id} className="border-l-2 pl-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                      <span className="capitalize">{anecdote.anecdote_type}</span>
                      {anecdote.date && (
                        <>
                          <span>•</span>
                          <span>{format(new Date(anecdote.date), 'MMM d, yyyy')}</span>
                        </>
                      )}
                    </div>
                    {anecdote.title && (
                      <h4 className="font-medium">{anecdote.title}</h4>
                    )}
                    <p className="text-sm">{anecdote.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">
                No anecdotes yet. Add memories, jokes, or notes!
              </p>
            )}
          </div>

          {/* Photos */}
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Photos</h3>
              <button
                onClick={() => setIsPhotoUploadOpen(true)}
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
              >
                <Camera className="h-4 w-4" />
                Upload
              </button>
            </div>
            <PhotoGallery photos={photos || []} personId={id} />
          </div>

          {/* Employment History */}
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Employment History</h3>
              <button
                onClick={() => setIsAddEmploymentOpen(true)}
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
              >
                <Briefcase className="h-4 w-4" />
                Add
              </button>
            </div>
            <EmploymentHistory employments={employments || []} personId={id!} />
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Relationships */}
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Relationships</h3>
              <button
                onClick={() => setIsAddRelationshipOpen(true)}
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
              >
                <Plus className="h-4 w-4" />
                Add
              </button>
            </div>
            {relationships && relationships.length > 0 ? (
              <div className="space-y-3">
                {relationships.map((rel) => (
                  <div
                    key={rel.id}
                    className="flex items-center gap-3 p-2 rounded-md -mx-2 group"
                  >
                    <Link
                      to={`/people/${rel.person_a === id ? rel.person_b : rel.person_a}`}
                      className="flex items-center gap-3 flex-1 hover:bg-accent rounded-md transition-colors"
                    >
                      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-semibold">
                        {(rel.person_a === id ? rel.person_b_name : rel.person_a_name)
                          .charAt(0)
                          .toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-sm">
                          {rel.person_a === id ? rel.person_b_name : rel.person_a_name}
                        </p>
                        <p className="text-xs text-muted-foreground capitalize">
                          {rel.relationship_type_inverse_name}
                        </p>
                      </div>
                    </Link>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => setEditingRelationship(rel)}
                        className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground"
                        title="Edit relationship"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteRelationship(
                          rel.id,
                          rel.person_a === id ? rel.person_b_name : rel.person_a_name
                        )}
                        className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                        title="Remove relationship"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">No relationships yet.</p>
            )}
          </div>

          {/* Groups */}
          {person.groups.length > 0 && (
            <div className="bg-card border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Groups</h3>
              <div className="space-y-2">
                {person.groups.map((group) => (
                  <div
                    key={group.id}
                    className="px-3 py-2 rounded-md text-sm"
                    style={{ backgroundColor: group.color + '15' }}
                  >
                    {group.full_path}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Edit Person Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Person"
        size="xl"
      >
        <PersonForm
          person={person}
          onSuccess={() => setIsEditModalOpen(false)}
          onCancel={() => setIsEditModalOpen(false)}
        />
      </Modal>

      {/* Add Relationship Modal */}
      <AddRelationshipModal
        isOpen={isAddRelationshipOpen}
        onClose={() => setIsAddRelationshipOpen(false)}
        personId={id!}
        personName={person.full_name}
      />

      {/* Add Anecdote Modal */}
      <AddAnecdoteModal
        isOpen={isAddAnecdoteOpen}
        onClose={() => setIsAddAnecdoteOpen(false)}
        personId={id!}
        personName={person.full_name}
      />

      {/* Photo Upload Modal */}
      <PhotoUpload
        isOpen={isPhotoUploadOpen}
        onClose={() => setIsPhotoUploadOpen(false)}
        personId={id}
        personName={person.full_name}
      />

      {/* Add Employment Modal */}
      <AddEmploymentModal
        isOpen={isAddEmploymentOpen}
        onClose={() => setIsAddEmploymentOpen(false)}
        personId={id!}
        personName={person.full_name}
      />

      {/* Edit Relationship Modal */}
      {editingRelationship && (
        <EditRelationshipModal
          isOpen={!!editingRelationship}
          onClose={() => setEditingRelationship(null)}
          relationship={editingRelationship}
          currentPersonId={id!}
        />
      )}
    </div>
  )
}
