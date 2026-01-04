import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Network, Filter, ZoomIn, Users, RefreshCw } from 'lucide-react'
import { getRelationshipGraph, getPersons, getRelationshipTypes } from '@/services/api'
import { RelationshipGraph } from '@/components/RelationshipGraph'

export function GraphPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // Get filter params from URL
  const centerId = searchParams.get('center') || ''
  const depth = parseInt(searchParams.get('depth') || '2', 10)
  const category = searchParams.get('category') || ''

  // Local state for filter UI
  const [centerFilter, setCenterFilter] = useState(centerId)
  const [depthFilter, setDepthFilter] = useState(depth)
  const [categoryFilter, setCategoryFilter] = useState(category)

  // Fetch graph data
  const {
    data: graphData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['relationship-graph', { center_id: centerId, depth, category }],
    queryFn: () =>
      getRelationshipGraph({
        center_id: centerId || undefined,
        depth,
        category: category || undefined,
      }),
  })

  // Fetch persons for center selector
  const { data: personsResponse } = useQuery({
    queryKey: ['persons-list'],
    queryFn: () => getPersons({ page: 1 }),
  })

  // Fetch relationship types for category filter
  const { data: typesResponse } = useQuery({
    queryKey: ['relationship-types'],
    queryFn: getRelationshipTypes,
  })

  const persons = personsResponse?.results || []
  const types = typesResponse?.results || []

  // Get unique categories from types
  const categories = [...new Set(types.map((t) => t.category))].filter(Boolean)

  // Apply filters
  const applyFilters = () => {
    const params = new URLSearchParams()
    if (centerFilter) params.set('center', centerFilter)
    if (depthFilter !== 2) params.set('depth', String(depthFilter))
    if (categoryFilter) params.set('category', categoryFilter)
    setSearchParams(params)
  }

  // Reset filters
  const resetFilters = () => {
    setCenterFilter('')
    setDepthFilter(2)
    setCategoryFilter('')
    setSearchParams(new URLSearchParams())
  }

  // Handle node click - navigate to person detail or recenter
  const handleNodeClick = (nodeId: string) => {
    // Recenter on clicked node
    const params = new URLSearchParams(searchParams)
    params.set('center', nodeId)
    setSearchParams(params)
    setCenterFilter(nodeId)
  }

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Network className="h-6 w-6" />
            Relationship Graph
          </h1>
          <p className="text-muted-foreground">
            Visualize connections between people in your network
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md border hover:bg-accent"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-4 p-4 bg-card border rounded-lg">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filters:</span>
        </div>

        {/* Center person selector */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Center on Person</label>
          <select
            value={centerFilter}
            onChange={(e) => setCenterFilter(e.target.value)}
            className="px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-w-[200px]"
          >
            <option value="">Show All</option>
            {persons.map((person) => (
              <option key={person.id} value={person.id}>
                {person.full_name}
              </option>
            ))}
          </select>
        </div>

        {/* Depth selector */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Degrees of Separation</label>
          <select
            value={depthFilter}
            onChange={(e) => setDepthFilter(parseInt(e.target.value, 10))}
            className="px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="1">1 (Direct only)</option>
            <option value="2">2 (Friends of friends)</option>
            <option value="3">3 (Extended network)</option>
          </select>
        </div>

        {/* Category filter */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Relationship Category</label>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={applyFilters}
            className="px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-md hover:bg-primary/90"
          >
            Apply
          </button>
          <button
            onClick={resetFilters}
            className="px-4 py-2 border text-sm font-medium rounded-md hover:bg-accent"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <div className="text-2xl font-bold">{graphData?.nodes.length || 0}</div>
          </div>
          <div className="text-sm text-muted-foreground">People in View</div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Network className="h-4 w-4 text-muted-foreground" />
            <div className="text-2xl font-bold">{graphData?.edges.length || 0}</div>
          </div>
          <div className="text-sm text-muted-foreground">Connections</div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2">
            <ZoomIn className="h-4 w-4 text-muted-foreground" />
            <div className="text-2xl font-bold">{depth}</div>
          </div>
          <div className="text-sm text-muted-foreground">Depth Level</div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <div className="text-2xl font-bold">
              {graphData?.relationship_types.length || 0}
            </div>
          </div>
          <div className="text-sm text-muted-foreground">Relationship Types</div>
        </div>
      </div>

      {/* Graph */}
      <div className="flex-1 min-h-[500px]">
        {isLoading ? (
          <div className="h-full flex items-center justify-center bg-muted/30 rounded-lg border">
            <div className="text-muted-foreground flex items-center gap-2">
              <RefreshCw className="h-5 w-5 animate-spin" />
              Loading graph...
            </div>
          </div>
        ) : !graphData || graphData.nodes.length === 0 ? (
          <div className="h-full flex items-center justify-center bg-muted/30 rounded-lg border">
            <div className="text-center">
              <Network className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No connections to display</h3>
              <p className="text-muted-foreground mb-4">
                Add relationships between people to see the network graph
              </p>
              <button
                onClick={() => navigate('/people')}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
              >
                <Users className="h-4 w-4" />
                Go to People
              </button>
            </div>
          </div>
        ) : (
          <RelationshipGraph
            nodes={graphData.nodes}
            edges={graphData.edges}
            relationshipTypes={graphData.relationship_types}
            centerPersonId={graphData.center_person_id}
            onNodeClick={handleNodeClick}
          />
        )}
      </div>

      {/* Help text */}
      <div className="text-xs text-muted-foreground text-center pb-4">
        Click on a person node to center the graph on them. Use the mouse wheel to zoom,
        drag to pan.
      </div>
    </div>
  )
}
