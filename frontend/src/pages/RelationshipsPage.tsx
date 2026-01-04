import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Link2, Users, ArrowRight, Sparkles, Check, X, Loader2, Lightbulb } from 'lucide-react'
import { getRelationships, getRelationshipTypes, suggestRelationships, applyRelationshipSuggestion, type RelationshipSuggestion } from '@/services/api'
import { format } from 'date-fns'

export function RelationshipsPage() {
  const [typeFilter, setTypeFilter] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const queryClient = useQueryClient()

  const { data: relationshipsResponse, isLoading } = useQuery({
    queryKey: ['relationships', { relationship_type: typeFilter }],
    queryFn: () =>
      getRelationships({
        relationship_type: typeFilter || undefined,
      }),
  })

  const { data: typesResponse } = useQuery({
    queryKey: ['relationship-types'],
    queryFn: getRelationshipTypes,
  })

  const relationships = relationshipsResponse?.results || []
  const types = typesResponse?.results || []

  // AI Suggestions
  const {
    data: suggestionsData,
    isLoading: suggestionsLoading,
    refetch: refetchSuggestions,
  } = useQuery({
    queryKey: ['relationship-suggestions'],
    queryFn: suggestRelationships,
    enabled: showSuggestions,
  })

  const applyMutation = useMutation({
    mutationFn: (suggestion: RelationshipSuggestion) =>
      applyRelationshipSuggestion(
        suggestion.person1_id,
        suggestion.person2_id,
        suggestion.suggested_type
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['relationships'] })
      queryClient.invalidateQueries({ queryKey: ['relationship-suggestions'] })
    },
  })

  const [dismissedSuggestions, setDismissedSuggestions] = useState<Set<string>>(new Set())
  const dismissSuggestion = (suggestion: RelationshipSuggestion) => {
    setDismissedSuggestions(prev => new Set([...prev, `${suggestion.person1_id}-${suggestion.person2_id}`]))
  }

  const activeSuggestions = suggestionsData?.suggestions.filter(
    s => !dismissedSuggestions.has(`${s.person1_id}-${s.person2_id}`)
  ) || []

  // Group relationships by type
  const groupedRelationships = relationships.reduce(
    (acc, rel) => {
      const type = rel.relationship_type_name
      if (!acc[type]) acc[type] = []
      acc[type].push(rel)
      return acc
    },
    {} as Record<string, typeof relationships>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Relationships</h1>
          <p className="text-muted-foreground">
            View connections between people in your network
          </p>
        </div>
        <button
          onClick={() => {
            setShowSuggestions(!showSuggestions)
            if (!showSuggestions) {
              refetchSuggestions()
            }
          }}
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            showSuggestions
              ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }`}
        >
          <Sparkles className="h-4 w-4" />
          {showSuggestions ? 'Hide Suggestions' : 'AI Suggestions'}
        </button>
      </div>

      {/* AI Suggestions Panel */}
      {showSuggestions && (
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/30 dark:to-pink-950/30 border border-purple-200 dark:border-purple-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              <h3 className="font-semibold text-purple-900 dark:text-purple-100">
                AI Relationship Suggestions
              </h3>
            </div>
            {suggestionsData && (
              <span className="text-sm text-muted-foreground">
                Analyzed {suggestionsData.total_contacts} contacts • {suggestionsData.existing_relationships_count} existing relationships
              </span>
            )}
          </div>

          {suggestionsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-purple-600" />
              <span className="ml-2 text-muted-foreground">Analyzing your contacts...</span>
            </div>
          ) : activeSuggestions.length === 0 ? (
            <div className="text-center py-8">
              <Sparkles className="h-8 w-8 mx-auto text-purple-400 mb-2" />
              <p className="text-muted-foreground">
                {suggestionsData?.message || 'No new relationship suggestions found.'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Add more contacts or photos together to get suggestions.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeSuggestions.map((suggestion) => (
                <SuggestionCard
                  key={`${suggestion.person1_id}-${suggestion.person2_id}`}
                  suggestion={suggestion}
                  onApply={() => applyMutation.mutate(suggestion)}
                  onDismiss={() => dismissSuggestion(suggestion)}
                  isApplying={applyMutation.isPending}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border rounded-lg p-4">
          <div className="text-2xl font-bold">{relationships.length}</div>
          <div className="text-sm text-muted-foreground">Total Connections</div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="text-2xl font-bold">{types.length}</div>
          <div className="text-sm text-muted-foreground">Relationship Types</div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="text-2xl font-bold">
            {types.filter((t) => t.category === 'family').length}
          </div>
          <div className="text-sm text-muted-foreground">Family Types</div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="text-2xl font-bold">
            {types.filter((t) => t.category === 'professional').length}
          </div>
          <div className="text-sm text-muted-foreground">Professional Types</div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-4">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Relationship Types</option>
          {types.map((type) => (
            <option key={type.id} value={type.id}>
              {type.name}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="text-muted-foreground">Loading relationships...</div>
      ) : relationships.length === 0 ? (
        <div className="bg-card border rounded-lg p-12 text-center">
          <Link2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No relationships yet</h3>
          <p className="text-muted-foreground mb-4">
            Add relationships from person profiles to see connections here
          </p>
          <Link
            to="/people"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
          >
            <Users className="h-4 w-4" />
            Go to People
          </Link>
        </div>
      ) : typeFilter ? (
        // Single type view
        <div className="bg-card border rounded-lg divide-y">
          {relationships.map((rel) => (
            <RelationshipRow key={rel.id} relationship={rel} />
          ))}
        </div>
      ) : (
        // Grouped by type view
        <div className="space-y-6">
          {Object.entries(groupedRelationships).map(([typeName, rels]) => (
            <div key={typeName} className="bg-card border rounded-lg overflow-hidden">
              <div className="px-4 py-3 bg-muted/50 border-b">
                <h3 className="font-medium flex items-center gap-2">
                  <Link2 className="h-4 w-4" />
                  {typeName}
                  <span className="text-muted-foreground font-normal">
                    ({rels.length})
                  </span>
                </h3>
              </div>
              <div className="divide-y">
                {rels.slice(0, 5).map((rel) => (
                  <RelationshipRow key={rel.id} relationship={rel} />
                ))}
                {rels.length > 5 && (
                  <div className="px-4 py-3 text-center">
                    <button
                      onClick={() => {
                        const type = types.find((t) => t.name === typeName)
                        if (type) setTypeFilter(type.id)
                      }}
                      className="text-sm text-primary hover:underline"
                    >
                      View all {rels.length} {typeName.toLowerCase()} relationships
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface RelationshipRowProps {
  relationship: {
    id: string
    person_a: string
    person_a_name: string
    person_b: string
    person_b_name: string
    relationship_type_name: string
    started_date: string | null
    strength: number | null
  }
}

function RelationshipRow({ relationship }: RelationshipRowProps) {
  return (
    <div className="flex items-center gap-4 px-4 py-3 hover:bg-accent/50 transition-colors">
      {/* Person A */}
      <Link
        to={`/people/${relationship.person_a}`}
        className="flex items-center gap-2 hover:text-primary"
      >
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-semibold">
          {relationship.person_a_name.charAt(0).toUpperCase()}
        </div>
        <span className="font-medium">{relationship.person_a_name}</span>
      </Link>

      {/* Arrow */}
      <div className="flex items-center gap-2 text-muted-foreground">
        <ArrowRight className="h-4 w-4" />
        <span className="text-xs uppercase tracking-wide">
          {relationship.relationship_type_name}
        </span>
        <ArrowRight className="h-4 w-4" />
      </div>

      {/* Person B */}
      <Link
        to={`/people/${relationship.person_b}`}
        className="flex items-center gap-2 hover:text-primary"
      >
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-semibold">
          {relationship.person_b_name.charAt(0).toUpperCase()}
        </div>
        <span className="font-medium">{relationship.person_b_name}</span>
      </Link>

      {/* Meta */}
      <div className="ml-auto flex items-center gap-4 text-sm text-muted-foreground">
        {relationship.strength && (
          <div className="flex items-center gap-1">
            <span>Strength:</span>
            <div className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className={`h-2 w-2 rounded-full ${
                    i <= relationship.strength! ? 'bg-primary' : 'bg-muted'
                  }`}
                />
              ))}
            </div>
          </div>
        )}
        {relationship.started_date && (
          <span>Since {format(new Date(relationship.started_date), 'MMM yyyy')}</span>
        )}
      </div>
    </div>
  )
}

interface SuggestionCardProps {
  suggestion: RelationshipSuggestion
  onApply: () => void
  onDismiss: () => void
  isApplying: boolean
}

function SuggestionCard({ suggestion, onApply, onDismiss, isApplying }: SuggestionCardProps) {
  const confidenceColor =
    suggestion.confidence >= 0.8
      ? 'text-green-600 dark:text-green-400'
      : suggestion.confidence >= 0.6
        ? 'text-yellow-600 dark:text-yellow-400'
        : 'text-orange-600 dark:text-orange-400'

  return (
    <div className="bg-white dark:bg-card border rounded-lg p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          {/* People involved */}
          <div className="flex items-center gap-2 mb-2">
            <Link
              to={`/people/${suggestion.person1_id}`}
              className="font-medium text-primary hover:underline"
            >
              {suggestion.person1_name}
            </Link>
            <span className="text-muted-foreground">→</span>
            <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 rounded text-sm font-medium">
              {suggestion.suggested_type}
            </span>
            <span className="text-muted-foreground">→</span>
            <Link
              to={`/people/${suggestion.person2_id}`}
              className="font-medium text-primary hover:underline"
            >
              {suggestion.person2_name}
            </Link>
          </div>

          {/* Reason */}
          <p className="text-sm text-muted-foreground mb-2">{suggestion.reason}</p>

          {/* Evidence */}
          {suggestion.evidence.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {suggestion.evidence.map((e, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 bg-muted rounded-full"
                >
                  {e}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col items-end gap-2">
          <span className={`text-sm font-medium ${confidenceColor}`}>
            {Math.round(suggestion.confidence * 100)}% confident
          </span>
          <div className="flex gap-2">
            <button
              onClick={onDismiss}
              className="p-2 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              title="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
            <button
              onClick={onApply}
              disabled={isApplying}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium disabled:opacity-50 transition-colors"
            >
              {isApplying ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              Accept
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
