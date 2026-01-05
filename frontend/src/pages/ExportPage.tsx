import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Download,
  FileJson,
  FileSpreadsheet,
  Loader2,
  Users,
  Link2,
  BookOpen,
  Image,
  Tags,
  FolderTree,
  CheckCircle2,
  Database,
} from 'lucide-react'
import { getExportPreview, downloadExport, type ExportPreviewResponse } from '@/services/api'

type EntityType = 'persons' | 'relationships' | 'anecdotes' | 'photos' | 'tags' | 'groups' | 'relationship_types'

const ENTITY_INFO: Record<EntityType, { icon: typeof Users; label: string; csvSupported: boolean }> = {
  persons: { icon: Users, label: 'People', csvSupported: true },
  relationships: { icon: Link2, label: 'Relationships', csvSupported: true },
  anecdotes: { icon: BookOpen, label: 'Anecdotes', csvSupported: true },
  photos: { icon: Image, label: 'Photos', csvSupported: false },
  tags: { icon: Tags, label: 'Tags', csvSupported: false },
  groups: { icon: FolderTree, label: 'Groups', csvSupported: false },
  relationship_types: { icon: Link2, label: 'Relationship Types', csvSupported: false },
}

export function ExportPage() {
  const [selectedEntity, setSelectedEntity] = useState<EntityType | 'all'>('all')
  const [selectedFormat, setSelectedFormat] = useState<'json' | 'csv'>('json')
  const [exportSuccess, setExportSuccess] = useState(false)

  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ['export-preview'],
    queryFn: () => getExportPreview(),
  })

  const exportMutation = useMutation({
    mutationFn: async () => {
      await downloadExport(
        selectedFormat,
        selectedEntity === 'all' ? undefined : selectedEntity
      )
    },
    onSuccess: () => {
      setExportSuccess(true)
      setTimeout(() => setExportSuccess(false), 3000)
    },
  })

  // Get entity counts from preview
  const getCounts = (previewData: ExportPreviewResponse | undefined): Record<EntityType, number> => {
    if (!previewData?.counts) {
      return {
        persons: 0,
        relationships: 0,
        relationship_types: 0,
        anecdotes: 0,
        photos: 0,
        tags: 0,
        groups: 0,
      }
    }
    return previewData.counts
  }

  const counts = getCounts(preview)

  // Check if selected combination is valid
  const isValidSelection = () => {
    if (selectedFormat === 'json') return true
    if (selectedEntity === 'all') return false
    return ENTITY_INFO[selectedEntity]?.csvSupported ?? false
  }

  // Handle entity selection
  const handleEntitySelect = (entity: EntityType | 'all') => {
    setSelectedEntity(entity)
    // If CSV is selected and new entity doesn't support CSV, switch to JSON
    if (selectedFormat === 'csv') {
      if (entity === 'all' || !ENTITY_INFO[entity as EntityType]?.csvSupported) {
        setSelectedFormat('json')
      }
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Download className="h-6 w-6" />
          Export Data
        </h1>
        <p className="text-muted-foreground">
          Export your data in JSON or CSV format for backup or migration
        </p>
      </div>

      {/* Preview Stats */}
      {previewLoading ? (
        <div className="bg-card border rounded-lg p-8 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : preview?.counts ? (
        <div className="bg-card border rounded-lg p-6">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Database className="h-5 w-5" />
            Data Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(Object.entries(ENTITY_INFO) as [EntityType, typeof ENTITY_INFO[EntityType]][]).map(
              ([key, { icon: Icon, label }]) => (
                <div
                  key={key}
                  className="flex items-center gap-3 p-3 rounded-lg bg-muted/50"
                >
                  <Icon className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">{label}</p>
                    <p className="text-2xl font-bold">{counts[key] ?? 0}</p>
                  </div>
                </div>
              )
            )}
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Total items: <span className="font-medium">{preview.total_items}</span>
          </p>
        </div>
      ) : null}

      {/* Export Options */}
      <div className="bg-card border rounded-lg p-6 space-y-6">
        {/* Data Selection */}
        <div>
          <h3 className="font-medium mb-3">What to Export</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <button
              onClick={() => handleEntitySelect('all')}
              className={`p-3 rounded-lg border text-left transition-colors ${
                selectedEntity === 'all'
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'hover:bg-muted'
              }`}
            >
              <Database className="h-5 w-5 mb-1" />
              <p className="font-medium text-sm">All Data</p>
              <p className="text-xs text-muted-foreground">Complete export</p>
            </button>
            {(Object.entries(ENTITY_INFO) as [EntityType, typeof ENTITY_INFO[EntityType]][]).map(
              ([key, { icon: Icon, label }]) => (
                <button
                  key={key}
                  onClick={() => handleEntitySelect(key)}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    selectedEntity === key
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'hover:bg-muted'
                  }`}
                >
                  <Icon className="h-5 w-5 mb-1" />
                  <p className="font-medium text-sm">{label}</p>
                  <p className="text-xs text-muted-foreground">{counts[key] ?? 0} items</p>
                </button>
              )
            )}
          </div>
        </div>

        {/* Format Selection */}
        <div>
          <h3 className="font-medium mb-3">Export Format</h3>
          <div className="flex gap-3">
            <button
              onClick={() => setSelectedFormat('json')}
              className={`flex-1 p-4 rounded-lg border text-left transition-colors ${
                selectedFormat === 'json'
                  ? 'border-primary bg-primary/10'
                  : 'hover:bg-muted'
              }`}
            >
              <div className="flex items-center gap-3">
                <FileJson
                  className={`h-8 w-8 ${
                    selectedFormat === 'json' ? 'text-primary' : 'text-muted-foreground'
                  }`}
                />
                <div>
                  <p className="font-medium">JSON</p>
                  <p className="text-sm text-muted-foreground">
                    Complete data with all relationships
                  </p>
                </div>
              </div>
            </button>
            <button
              onClick={() => {
                if (selectedEntity === 'all' || !ENTITY_INFO[selectedEntity as EntityType]?.csvSupported) {
                  // Can't select CSV for all or unsupported entities
                  return
                }
                setSelectedFormat('csv')
              }}
              disabled={selectedEntity === 'all' || !ENTITY_INFO[selectedEntity as EntityType]?.csvSupported}
              className={`flex-1 p-4 rounded-lg border text-left transition-colors ${
                selectedFormat === 'csv'
                  ? 'border-primary bg-primary/10'
                  : selectedEntity === 'all' || !ENTITY_INFO[selectedEntity as EntityType]?.csvSupported
                  ? 'opacity-50 cursor-not-allowed'
                  : 'hover:bg-muted'
              }`}
            >
              <div className="flex items-center gap-3">
                <FileSpreadsheet
                  className={`h-8 w-8 ${
                    selectedFormat === 'csv' ? 'text-primary' : 'text-muted-foreground'
                  }`}
                />
                <div>
                  <p className="font-medium">CSV</p>
                  <p className="text-sm text-muted-foreground">
                    Spreadsheet format (People, Relationships, Anecdotes)
                  </p>
                </div>
              </div>
            </button>
          </div>
          {selectedFormat === 'json' && selectedEntity === 'all' && (
            <p className="mt-2 text-sm text-muted-foreground">
              JSON export includes all data types with complete relationships and metadata.
            </p>
          )}
          {(selectedEntity === 'all' || !ENTITY_INFO[selectedEntity as EntityType]?.csvSupported) &&
            selectedFormat === 'json' && (
              <p className="mt-2 text-xs text-muted-foreground">
                CSV is only available for People, Relationships, and Anecdotes when exporting
                individual entity types.
              </p>
            )}
        </div>

        {/* Export Button */}
        <div className="pt-4 border-t">
          <button
            onClick={() => exportMutation.mutate()}
            disabled={!isValidSelection() || exportMutation.isPending}
            className="w-full py-3 px-4 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
          >
            {exportMutation.isPending ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Preparing export...
              </>
            ) : exportSuccess ? (
              <>
                <CheckCircle2 className="h-5 w-5" />
                Export downloaded!
              </>
            ) : (
              <>
                <Download className="h-5 w-5" />
                Download {selectedEntity === 'all' ? 'All Data' : ENTITY_INFO[selectedEntity]?.label}{' '}
                as {selectedFormat.toUpperCase()}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Export Info */}
      <div className="bg-muted/50 rounded-lg p-4 text-sm text-muted-foreground">
        <h3 className="font-medium text-foreground mb-2">About Exports</h3>
        <ul className="list-disc list-inside space-y-1">
          <li>
            <strong>JSON</strong> exports include all data with complete metadata and
            relationships. Ideal for backup and restore.
          </li>
          <li>
            <strong>CSV</strong> exports are suitable for spreadsheet applications and data
            analysis.
          </li>
          <li>
            Photo files are not included in exports - only photo metadata (captions,
            dates, tags).
          </li>
          <li>Export files are named with the current date for easy tracking.</li>
        </ul>
      </div>

      {/* Error Display */}
      {exportMutation.isError && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 text-destructive">
          <p className="font-medium">Export failed</p>
          <p className="text-sm">
            {exportMutation.error instanceof Error
              ? exportMutation.error.message
              : 'An error occurred while exporting data'}
          </p>
        </div>
      )}
    </div>
  )
}
