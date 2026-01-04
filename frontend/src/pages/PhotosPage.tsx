import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Image, Calendar, MapPin, User, X, ChevronLeft, ChevronRight } from 'lucide-react'
import { getPhotos } from '@/services/api'
import { format } from 'date-fns'
import type { Photo } from '@/types'
import { PhotoUpload } from '@/components/PhotoUpload'

export function PhotosPage() {
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null)
  const [isUploadOpen, setIsUploadOpen] = useState(false)

  const { data: photosResponse, isLoading } = useQuery({
    queryKey: ['photos'],
    queryFn: () => getPhotos(),
  })

  const photos = photosResponse?.results || []

  const handlePrevious = () => {
    if (!selectedPhoto) return
    const currentIndex = photos.findIndex((p) => p.id === selectedPhoto.id)
    if (currentIndex > 0) {
      setSelectedPhoto(photos[currentIndex - 1])
    }
  }

  const handleNext = () => {
    if (!selectedPhoto) return
    const currentIndex = photos.findIndex((p) => p.id === selectedPhoto.id)
    if (currentIndex < photos.length - 1) {
      setSelectedPhoto(photos[currentIndex + 1])
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') setSelectedPhoto(null)
    if (e.key === 'ArrowLeft') handlePrevious()
    if (e.key === 'ArrowRight') handleNext()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Photos</h1>
          <p className="text-muted-foreground">
            Browse all photos across your contacts
          </p>
        </div>
        <button
          onClick={() => setIsUploadOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Upload Photo
        </button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="text-muted-foreground">Loading photos...</div>
      ) : photos.length === 0 ? (
        <div className="bg-card border rounded-lg p-12 text-center">
          <Image className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No photos yet</h3>
          <p className="text-muted-foreground mb-4">
            Upload photos to remember moments with the people in your life
          </p>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Upload your first photo
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {photos.map((photo) => (
            <button
              key={photo.id}
              onClick={() => setSelectedPhoto(photo)}
              className="group relative aspect-square rounded-lg overflow-hidden bg-muted hover:ring-2 hover:ring-primary transition-all"
            >
              <img
                src={photo.file}
                alt={photo.caption || 'Photo'}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform"
              />
              {/* Overlay on hover */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors">
                <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  {photo.persons.length > 0 && (
                    <div className="flex items-center gap-1 text-white text-xs">
                      <User className="h-3 w-3" />
                      <span className="truncate">
                        {photo.persons.map((p) => p.full_name).join(', ')}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Lightbox */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={() => setSelectedPhoto(null)}
          onKeyDown={handleKeyDown}
          tabIndex={0}
        >
          {/* Close button */}
          <button
            onClick={() => setSelectedPhoto(null)}
            className="absolute top-4 right-4 p-2 text-white/70 hover:text-white"
          >
            <X className="h-6 w-6" />
          </button>

          {/* Navigation */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              handlePrevious()
            }}
            className="absolute left-4 p-2 text-white/70 hover:text-white disabled:opacity-30"
            disabled={photos.findIndex((p) => p.id === selectedPhoto.id) === 0}
          >
            <ChevronLeft className="h-8 w-8" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation()
              handleNext()
            }}
            className="absolute right-4 p-2 text-white/70 hover:text-white disabled:opacity-30"
            disabled={
              photos.findIndex((p) => p.id === selectedPhoto.id) === photos.length - 1
            }
          >
            <ChevronRight className="h-8 w-8" />
          </button>

          {/* Photo and info */}
          <div
            className="flex flex-col lg:flex-row max-w-7xl max-h-[90vh] mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Image */}
            <div className="flex-1 flex items-center justify-center">
              <img
                src={selectedPhoto.file}
                alt={selectedPhoto.caption || 'Photo'}
                className="max-h-[70vh] lg:max-h-[85vh] max-w-full object-contain rounded-lg"
              />
            </div>

            {/* Info panel */}
            <div className="lg:w-80 bg-card rounded-lg p-4 mt-4 lg:mt-0 lg:ml-4 overflow-auto max-h-[40vh] lg:max-h-[85vh]">
              {selectedPhoto.caption && (
                <p className="text-sm mb-4">{selectedPhoto.caption}</p>
              )}

              <div className="space-y-3 text-sm">
                {selectedPhoto.date_taken && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>
                      {format(new Date(selectedPhoto.date_taken), 'MMMM d, yyyy')}
                    </span>
                  </div>
                )}

                {selectedPhoto.location && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    <span>{selectedPhoto.location}</span>
                  </div>
                )}

                {selectedPhoto.persons.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 text-muted-foreground mb-2">
                      <User className="h-4 w-4" />
                      <span>People in photo</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {selectedPhoto.persons.map((person) => (
                        <Link
                          key={person.id}
                          to={`/people/${person.id}`}
                          className="inline-flex items-center gap-2 px-3 py-1.5 bg-accent rounded-full text-sm hover:bg-accent/80"
                        >
                          <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium">
                            {person.first_name.charAt(0).toUpperCase()}
                          </div>
                          {person.full_name}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}

                {selectedPhoto.ai_description && (
                  <div className="pt-3 border-t">
                    <p className="text-xs text-muted-foreground mb-1">AI Description</p>
                    <p className="text-sm">{selectedPhoto.ai_description}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Photo Upload Modal */}
      <PhotoUpload
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
      />
    </div>
  )
}
