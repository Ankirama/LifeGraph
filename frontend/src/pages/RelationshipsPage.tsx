import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Link2, Users, ArrowRight } from 'lucide-react'
import { getRelationships, getRelationshipTypes } from '@/services/api'
import { format } from 'date-fns'

export function RelationshipsPage() {
  const [typeFilter, setTypeFilter] = useState('')

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
      </div>

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
