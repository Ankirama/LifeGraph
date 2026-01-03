import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Edit, Calendar, MapPin, Mail, Phone } from 'lucide-react'
import { getPerson, getPersonRelationships, getPersonAnecdotes } from '@/services/api'
import { format } from 'date-fns'

export function PersonDetail() {
  const { id } = useParams<{ id: string }>()

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
              {person.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-2xl font-bold">{person.name}</h2>
              {person.nickname && (
                <p className="text-muted-foreground">"{person.nickname}"</p>
              )}
            </div>
          </div>
        </div>
        <button className="inline-flex items-center gap-2 border px-4 py-2 rounded-md text-sm font-medium hover:bg-accent">
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
          {person.ai_summary && (
            <div className="bg-card border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">AI Summary</h3>
              <p className="text-muted-foreground">{person.ai_summary}</p>
            </div>
          )}

          {/* Notes */}
          {person.notes && (
            <div className="bg-card border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Notes</h3>
              <p className="whitespace-pre-wrap">{person.notes}</p>
            </div>
          )}

          {/* Anecdotes */}
          <div className="bg-card border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Anecdotes</h3>
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
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Relationships */}
          <div className="bg-card border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Relationships</h3>
            {relationships && relationships.length > 0 ? (
              <div className="space-y-3">
                {relationships.map((rel) => (
                  <Link
                    key={rel.id}
                    to={`/people/${rel.person_a === id ? rel.person_b : rel.person_a}`}
                    className="flex items-center gap-3 hover:bg-accent p-2 rounded-md transition-colors -mx-2"
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
                      <p className="text-xs text-muted-foreground">
                        {rel.relationship_type_name}
                      </p>
                    </div>
                  </Link>
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
    </div>
  )
}
