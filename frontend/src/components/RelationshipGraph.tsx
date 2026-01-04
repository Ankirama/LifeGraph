import { useCallback, useEffect, useMemo } from 'react'
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { GraphNode, GraphEdge, GraphRelationshipType } from '@/types'

// Category colors
const CATEGORY_COLORS: Record<string, string> = {
  family: '#ef4444', // red
  professional: '#3b82f6', // blue
  social: '#22c55e', // green
  custom: '#a855f7', // purple
}

interface PersonNodeData {
  label: string
  firstName: string
  lastName: string
  avatar: string | null
  isCenter: boolean
  [key: string]: unknown
}

// Custom node component for persons
function PersonNode({ data }: { data: PersonNodeData }) {
  const initials = `${data.firstName?.charAt(0) || ''}${data.lastName?.charAt(0) || ''}`.toUpperCase()

  return (
    <div
      className={`relative px-4 py-3 rounded-lg border-2 bg-card shadow-md transition-all hover:shadow-lg ${
        data.isCenter ? 'border-primary ring-2 ring-primary/30' : 'border-border'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-muted-foreground" />
      <Handle type="source" position={Position.Bottom} className="!bg-muted-foreground" />

      <div className="flex items-center gap-3">
        {data.avatar ? (
          <img
            src={data.avatar}
            alt={data.label}
            className="h-10 w-10 rounded-full object-cover"
          />
        ) : (
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold">
            {initials}
          </div>
        )}
        <div>
          <div className="font-medium text-sm">{data.label}</div>
          {data.isCenter && (
            <div className="text-xs text-muted-foreground">Center</div>
          )}
        </div>
      </div>
    </div>
  )
}

const nodeTypes = {
  person: PersonNode,
}

interface RelationshipGraphProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  relationshipTypes: GraphRelationshipType[]
  centerPersonId: string | null
  onNodeClick?: (nodeId: string) => void
}

export function RelationshipGraph({
  nodes,
  edges,
  relationshipTypes: _relationshipTypes,
  centerPersonId,
  onNodeClick,
}: RelationshipGraphProps) {
  // Convert graph data to React Flow format
  const flowNodes = useMemo(() => {
    // Calculate positions using a simple force-directed-like layout
    const nodeCount = nodes.length
    const centerX = 400
    const centerY = 300
    const radius = Math.max(200, nodeCount * 30)

    return nodes.map((node, index) => {
      const isCenter = node.id === centerPersonId

      // Position center node in the middle, others in a circle
      let x: number, y: number
      if (isCenter) {
        x = centerX
        y = centerY
      } else {
        const angle = (2 * Math.PI * index) / (nodeCount - (centerPersonId ? 1 : 0))
        x = centerX + radius * Math.cos(angle)
        y = centerY + radius * Math.sin(angle)
      }

      return {
        id: node.id,
        type: 'person',
        position: { x, y },
        data: {
          label: node.label,
          firstName: node.first_name,
          lastName: node.last_name,
          avatar: node.avatar,
          isCenter,
        } as PersonNodeData,
      }
    })
  }, [nodes, centerPersonId])

  const flowEdges = useMemo(() => {
    return edges.map((edge) => {
      const color = CATEGORY_COLORS[edge.category] || CATEGORY_COLORS.custom

      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.type_name,
        labelStyle: { fontSize: 10, fill: color },
        labelBgStyle: { fill: 'white', fillOpacity: 0.8 },
        style: {
          stroke: color,
          strokeWidth: edge.strength ? Math.min(edge.strength, 3) : 1,
        },
        markerEnd: edge.is_symmetric
          ? undefined
          : {
              type: MarkerType.ArrowClosed,
              color,
            },
        animated: false,
      }
    })
  }, [edges])

  const [nodesState, setNodes, onNodesChange] = useNodesState(flowNodes)
  const [edgesState, setEdges, onEdgesChange] = useEdgesState(flowEdges)

  // Update nodes/edges when props change
  useEffect(() => {
    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [flowNodes, flowEdges, setNodes, setEdges])

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: { id: string }) => {
      onNodeClick?.(node.id)
    },
    [onNodeClick]
  )

  return (
    <div className="w-full h-full min-h-[500px] bg-muted/30 rounded-lg border">
      <ReactFlow
        nodes={nodesState}
        edges={edgesState}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
        }}
      >
        <Controls />
        <Background color="#e5e7eb" gap={20} />
      </ReactFlow>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-card border rounded-lg p-3 shadow-sm">
        <div className="text-xs font-medium mb-2">Relationship Types</div>
        <div className="space-y-1">
          {Object.entries(CATEGORY_COLORS).map(([category, color]) => (
            <div key={category} className="flex items-center gap-2 text-xs">
              <div
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="capitalize">{category}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
