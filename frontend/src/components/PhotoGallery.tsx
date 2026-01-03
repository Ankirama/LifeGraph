import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, MapPin, Calendar, ChevronLeft, ChevronRight, Trash2, Sparkles, Loader2 } from 'lucide-react'
import { deletePhoto, generatePhotoDescription } from '@/services/api'
import { format } from 'date-fns'
import type { Photo } from '@/types'

interface PhotoGalleryProps {
  photos: Photo[]
  personId?: string
}

export function PhotoGallery({ photos, personId }: PhotoGalleryProps) {
  const queryClient = useQueryClient()
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)

  const deleteMutation = useMutation({
    mutationFn: deletePhoto,
    onSuccess: () => {
      if (personId) {
        queryClient.invalidateQueries({ queryKey: ['person', personId, 'photos'] })
      }
      queryClient.invalidateQueries({ queryKey: ['photos'] })
      setSelectedIndex(null)
    },
  })

  const describeMutation = useMutation({
    mutationFn: generatePhotoDescription,
    onSuccess: () => {
      if (personId) {
        queryClient.invalidateQueries({ queryKey: ['person', personId, 'photos'] })
      }
      queryClient.invalidateQueries({ queryKey: ['photos'] })
    },
  })

  const selectedPhoto = selectedIndex !== null ? photos[selectedIndex] : null

  const handlePrevious = () => {
    if (selectedIndex !== null && selectedIndex > 0) {
      setSelectedIndex(selectedIndex - 1)
    }
  }

  const handleNext = () => {
    if (selectedIndex !== null && selectedIndex < photos.length - 1) {
      setSelectedIndex(selectedIndex + 1)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') handlePrevious()
    if (e.key === 'ArrowRight') handleNext()
    if (e.key === 'Escape') setSelectedIndex(null)
  }

  if (photos.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No photos yet. Upload some memories!
      </p>
    )
  }

  return (
    <>
      {/* Grid */}
      <div className="grid grid-cols-3 gap-2">
        {photos.map((photo, index) => (
          <button
            key={photo.id}
            onClick={() => setSelectedIndex(index)}
            className="aspect-square rounded-md overflow-hidden hover:ring-2 hover:ring-primary transition-all"
          >
            <img
              src={photo.file}
              alt={photo.caption || 'Photo'}
              className="w-full h-full object-cover"
            />
          </button>
        ))}
      </div>

      {/* Lightbox */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={() => setSelectedIndex(null)}
          onKeyDown={handleKeyDown}
          tabIndex={0}
        >
          {/* Close button */}
          <button
            onClick={() => setSelectedIndex(null)}
            className="absolute top-4 right-4 p-2 text-white/70 hover:text-white transition-colors"
          >
            <X className="h-6 w-6" />
          </button>

          {/* Navigation */}
          {selectedIndex !== null && selectedIndex > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handlePrevious()
              }}
              className="absolute left-4 p-2 text-white/70 hover:text-white transition-colors"
            >
              <ChevronLeft className="h-8 w-8" />
            </button>
          )}
          {selectedIndex !== null && selectedIndex < photos.length - 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleNext()
              }}
              className="absolute right-4 p-2 text-white/70 hover:text-white transition-colors"
            >
              <ChevronRight className="h-8 w-8" />
            </button>
          )}

          {/* Image */}
          <div
            onClick={(e) => e.stopPropagation()}
            className="max-w-4xl max-h-[80vh] flex flex-col"
          >
            <img
              src={selectedPhoto.file}
              alt={selectedPhoto.caption || 'Photo'}
              className="max-h-[70vh] object-contain"
            />

            {/* Photo Info */}
            <div className="bg-black/50 p-4 rounded-b-lg text-white">
              {selectedPhoto.caption && (
                <p className="text-lg mb-2">{selectedPhoto.caption}</p>
              )}
              <div className="flex flex-wrap gap-4 text-sm text-white/70">
                {selectedPhoto.date_taken && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {format(new Date(selectedPhoto.date_taken), 'MMMM d, yyyy')}
                  </span>
                )}
                {selectedPhoto.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    {selectedPhoto.location}
                  </span>
                )}
              </div>
              {selectedPhoto.ai_description && (
                <p className="mt-2 text-sm text-white/60 italic">
                  {selectedPhoto.ai_description}
                </p>
              )}
              {selectedPhoto.persons.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {selectedPhoto.persons.map((person) => (
                    <span
                      key={person.id}
                      className="px-2 py-0.5 bg-white/20 rounded text-xs"
                    >
                      {person.full_name}
                    </span>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="mt-3 pt-3 border-t border-white/20 flex justify-between">
                <button
                  onClick={() => describeMutation.mutate(selectedPhoto.id)}
                  disabled={describeMutation.isPending}
                  className="flex items-center gap-1 text-purple-400 hover:text-purple-300 text-sm disabled:opacity-50"
                >
                  {describeMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Describing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      {selectedPhoto.ai_description ? 'Regenerate Description' : 'AI Describe'}
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this photo?')) {
                      deleteMutation.mutate(selectedPhoto.id)
                    }
                  }}
                  disabled={deleteMutation.isPending}
                  className="flex items-center gap-1 text-red-400 hover:text-red-300 text-sm"
                >
                  <Trash2 className="h-4 w-4" />
                  {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>

          {/* Counter */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/70 text-sm">
            {(selectedIndex ?? 0) + 1} / {photos.length}
          </div>
        </div>
      )}
    </>
  )
}
