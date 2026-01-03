import { useState, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Upload, X, Image } from 'lucide-react'
import { Modal } from './Modal'
import { uploadPhoto, getPersons } from '@/services/api'

interface PhotoUploadProps {
  isOpen: boolean
  onClose: () => void
  personId?: string
  personName?: string
}

export function PhotoUpload({ isOpen, onClose, personId, personName }: PhotoUploadProps) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [caption, setCaption] = useState('')
  const [dateTaken, setDateTaken] = useState('')
  const [location, setLocation] = useState('')
  const [selectedPersonIds, setSelectedPersonIds] = useState<string[]>(
    personId ? [personId] : []
  )
  const [searchQuery, setSearchQuery] = useState('')

  const { data: persons } = useQuery({
    queryKey: ['persons', { search: searchQuery }],
    queryFn: () => getPersons({ search: searchQuery }),
    enabled: isOpen && !personId,
  })

  const uploadMutation = useMutation({
    mutationFn: uploadPhoto,
    onSuccess: () => {
      if (personId) {
        queryClient.invalidateQueries({ queryKey: ['person', personId, 'photos'] })
      }
      queryClient.invalidateQueries({ queryKey: ['photos'] })
      handleClose()
    },
  })

  const handleClose = () => {
    setPreview(null)
    setFile(null)
    setCaption('')
    setDateTaken('')
    setLocation('')
    setSelectedPersonIds(personId ? [personId] : [])
    setSearchQuery('')
    onClose()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      const reader = new FileReader()
      reader.onload = (event) => {
        setPreview(event.target?.result as string)
      }
      reader.readAsDataURL(selectedFile)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)
    if (caption) formData.append('caption', caption)
    if (dateTaken) formData.append('date_taken', dateTaken)
    if (location) formData.append('location', location)
    selectedPersonIds.forEach((id) => {
      formData.append('person_ids', id)
    })

    uploadMutation.mutate(formData)
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Upload Photo" size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {personName && (
          <p className="text-sm text-muted-foreground">
            Upload a photo for{' '}
            <span className="font-medium text-foreground">{personName}</span>
          </p>
        )}

        {/* File Upload */}
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />

          {preview ? (
            <div className="relative">
              <img
                src={preview}
                alt="Preview"
                className="w-full max-h-64 object-contain rounded-md border"
              />
              <button
                type="button"
                onClick={() => {
                  setPreview(null)
                  setFile(null)
                  if (fileInputRef.current) {
                    fileInputRef.current.value = ''
                  }
                }}
                className="absolute top-2 right-2 p-1 bg-black/50 text-white rounded-full hover:bg-black/70"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full p-8 border-2 border-dashed rounded-md hover:border-primary transition-colors flex flex-col items-center gap-2 text-muted-foreground"
            >
              <Upload className="h-8 w-8" />
              <span>Click to select an image</span>
              <span className="text-xs">or drag and drop</span>
            </button>
          )}
        </div>

        {/* Caption */}
        <div>
          <label className="block text-sm font-medium mb-1">Caption</label>
          <input
            type="text"
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="What's happening in this photo?"
          />
        </div>

        {/* Date and Location */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Date Taken</label>
            <input
              type="date"
              value={dateTaken}
              onChange={(e) => setDateTaken(e.target.value)}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Where was this taken?"
            />
          </div>
        </div>

        {/* Person Selection (if not pre-selected) */}
        {!personId && (
          <div>
            <label className="block text-sm font-medium mb-1">Tag People</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring mb-2"
              placeholder="Search for people to tag..."
            />
            <div className="max-h-32 overflow-y-auto border rounded-md">
              {persons?.results.map((person) => (
                <label
                  key={person.id}
                  className={`flex items-center gap-3 px-3 py-2 hover:bg-accent cursor-pointer ${
                    selectedPersonIds.includes(person.id) ? 'bg-accent' : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedPersonIds.includes(person.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedPersonIds((prev) => [...prev, person.id])
                      } else {
                        setSelectedPersonIds((prev) =>
                          prev.filter((id) => id !== person.id)
                        )
                      }
                    }}
                    className="rounded"
                  />
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-semibold">
                      {person.first_name.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm">{person.full_name}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Selected People Preview */}
        {selectedPersonIds.length > 0 && !personId && (
          <div className="flex flex-wrap gap-2">
            {selectedPersonIds.map((id) => {
              const person = persons?.results.find((p) => p.id === id)
              return person ? (
                <span
                  key={id}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 rounded text-sm"
                >
                  <Image className="h-3 w-3" />
                  {person.full_name}
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedPersonIds((prev) => prev.filter((pid) => pid !== id))
                    }
                    className="hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ) : null
            })}
          </div>
        )}

        {/* Error */}
        {uploadMutation.error && (
          <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
            Failed to upload photo. Please try again.
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
            disabled={uploadMutation.isPending || !file}
            className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Upload Photo'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
