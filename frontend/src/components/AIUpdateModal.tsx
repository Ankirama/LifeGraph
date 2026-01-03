import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from './Modal'
import {
  parseUpdatesWithAI,
  applyUpdates,
  type ParsedUpdate,
} from '@/services/api'
import { Sparkles, Trash2, Edit2, Check, X, Loader2, User, Calendar, MessageSquare, BookOpen } from 'lucide-react'

interface AIUpdateModalProps {
  isOpen: boolean
  onClose: () => void
}

type Step = 'input' | 'preview' | 'result'

export function AIUpdateModal({ isOpen, onClose }: AIUpdateModalProps) {
  const queryClient = useQueryClient()
  const [step, setStep] = useState<Step>('input')
  const [inputText, setInputText] = useState('')
  const [parsedUpdates, setParsedUpdates] = useState<ParsedUpdate[]>([])
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [updateResult, setUpdateResult] = useState<{
    persons_updated: number
    anecdotes_created: number
    errors: string[]
  } | null>(null)

  const parseMutation = useMutation({
    mutationFn: parseUpdatesWithAI,
    onSuccess: (data) => {
      setParsedUpdates(data.updates)
      setStep('preview')
    },
  })

  const applyMutation = useMutation({
    mutationFn: applyUpdates,
    onSuccess: (data) => {
      setUpdateResult({
        persons_updated: data.summary.persons_updated,
        anecdotes_created: data.summary.anecdotes_created,
        errors: data.errors,
      })
      setStep('result')
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      queryClient.invalidateQueries({ queryKey: ['anecdotes'] })
    },
  })

  const handleClose = () => {
    setStep('input')
    setInputText('')
    setParsedUpdates([])
    setEditingIndex(null)
    setUpdateResult(null)
    onClose()
  }

  const handleParse = () => {
    if (!inputText.trim()) return
    parseMutation.mutate(inputText)
  }

  const handleApply = () => {
    if (parsedUpdates.length === 0) return
    applyMutation.mutate(parsedUpdates)
  }

  const handleRemoveUpdate = (index: number) => {
    setParsedUpdates((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpdateEntry = (index: number, updates: Partial<ParsedUpdate>) => {
    setParsedUpdates((prev) =>
      prev.map((update, i) => (i === index ? { ...update, ...updates } : update))
    )
  }

  const exampleText = `My mom's birthday is March 15, 1960.
I remember she told me a story about how she met dad at a dance in Lyon.
Pierre got a promotion last month - he's now a senior engineer at Google!
Sophie mentioned she's allergic to peanuts.`

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={
        step === 'input'
          ? 'AI Update Contacts'
          : step === 'preview'
            ? 'Review Updates'
            : 'Updates Applied'
      }
      size="xl"
    >
      {step === 'input' && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 bg-primary/5 border border-primary/20 rounded-lg">
            <Sparkles className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-primary">AI-Powered Updates</p>
              <p className="text-muted-foreground mt-1">
                Describe updates or memories about your existing contacts. Reference them by name
                or relationship (my mom, Pierre, my friend Sophie). The AI will match them to your
                contacts and extract updates and memories.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              What would you like to update or remember?
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[200px]"
              placeholder={exampleText}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Tip: Include birthdays, memories, stories, quotes, or any new information about people you know.
            </p>
          </div>

          {parseMutation.error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
              {(parseMutation.error as Error).message || 'Failed to parse updates. Please try again.'}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium border rounded-md hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleParse}
              disabled={parseMutation.isPending || !inputText.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {parseMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Analyze with AI
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {step === 'preview' && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Review the parsed updates below. You can edit or remove entries before applying.
          </p>

          {parsedUpdates.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground border rounded-lg">
              No updates were found. Make sure you reference existing contacts by name or relationship.
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {parsedUpdates.map((update, index) => (
                <div
                  key={index}
                  className="p-4 border rounded-lg bg-card"
                >
                  {editingIndex === index ? (
                    <EditUpdateForm
                      update={update}
                      onSave={(updates) => {
                        handleUpdateEntry(index, updates)
                        setEditingIndex(null)
                      }}
                      onCancel={() => setEditingIndex(null)}
                    />
                  ) : (
                    <div className="space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          {update.matched_person_name ? (
                            <span className="font-medium">{update.matched_person_name}</span>
                          ) : (
                            <span className="text-yellow-600">
                              Unknown: "{update.match_value}" ({update.match_type})
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => setEditingIndex(index)}
                            className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground"
                            title="Edit"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRemoveUpdate(index)}
                            className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                            title="Remove"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                      {/* Field Updates */}
                      {Object.keys(update.field_updates).length > 0 && (
                        <div className="pl-6 space-y-1">
                          {update.field_updates.birthday && (
                            <div className="flex items-center gap-2 text-sm">
                              <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                              <span>Birthday: {update.field_updates.birthday}</span>
                            </div>
                          )}
                          {update.field_updates.nickname && (
                            <div className="flex items-center gap-2 text-sm">
                              <span className="text-muted-foreground">Nickname:</span>
                              <span>"{update.field_updates.nickname}"</span>
                            </div>
                          )}
                          {update.field_updates.notes_to_append && (
                            <div className="flex items-start gap-2 text-sm">
                              <MessageSquare className="h-3.5 w-3.5 text-muted-foreground mt-0.5" />
                              <span className="text-muted-foreground line-clamp-2">
                                {update.field_updates.notes_to_append}
                              </span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Anecdotes */}
                      {update.anecdotes.length > 0 && (
                        <div className="pl-6 space-y-2">
                          {update.anecdotes.map((anecdote, aIndex) => (
                            <div key={aIndex} className="p-2 bg-muted/50 rounded text-sm">
                              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                                <BookOpen className="h-3 w-3" />
                                <span className="capitalize">{anecdote.anecdote_type}</span>
                                {anecdote.date && <span>({anecdote.date})</span>}
                                {anecdote.location && <span>@ {anecdote.location}</span>}
                              </div>
                              {anecdote.title && (
                                <p className="font-medium text-sm">{anecdote.title}</p>
                              )}
                              <p className="line-clamp-2">{anecdote.content}</p>
                            </div>
                          ))}
                        </div>
                      )}

                      {!update.matched_person_id && (
                        <p className="text-xs text-yellow-600 pl-6">
                          This person was not found in your contacts. The update will be skipped.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {applyMutation.error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
              {(applyMutation.error as Error).message || 'Failed to apply updates. Please try again.'}
            </div>
          )}

          <div className="flex justify-between gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => setStep('input')}
              className="px-4 py-2 text-sm font-medium border rounded-md hover:bg-accent"
            >
              Back to Edit
            </button>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-sm font-medium border rounded-md hover:bg-accent"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleApply}
                disabled={applyMutation.isPending || parsedUpdates.filter(u => u.matched_person_id).length === 0}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
              >
                {applyMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Applying...
                  </>
                ) : (
                  <>Apply {parsedUpdates.filter(u => u.matched_person_id).length} Update{parsedUpdates.filter(u => u.matched_person_id).length !== 1 ? 's' : ''}</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {step === 'result' && updateResult && (
        <div className="space-y-4">
          <div className="p-6 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
              <Check className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold">Updates Applied!</h3>
            <p className="text-muted-foreground mt-1">
              {updateResult.persons_updated > 0 && (
                <>Updated {updateResult.persons_updated} contact{updateResult.persons_updated !== 1 ? 's' : ''}</>
              )}
              {updateResult.persons_updated > 0 && updateResult.anecdotes_created > 0 && ' and '}
              {updateResult.anecdotes_created > 0 && (
                <>created {updateResult.anecdotes_created} anecdote{updateResult.anecdotes_created !== 1 ? 's' : ''}</>
              )}
              {updateResult.persons_updated === 0 && updateResult.anecdotes_created === 0 && (
                <>No changes were made</>
              )}
            </p>
          </div>

          {updateResult.errors.length > 0 && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="font-medium text-yellow-800 text-sm">Some issues occurred:</p>
              <ul className="mt-2 space-y-1 text-sm text-yellow-700">
                {updateResult.errors.map((error, i) => (
                  <li key={i}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex justify-center pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}

interface EditUpdateFormProps {
  update: ParsedUpdate
  onSave: (updates: Partial<ParsedUpdate>) => void
  onCancel: () => void
}

function EditUpdateForm({ update, onSave, onCancel }: EditUpdateFormProps) {
  const [birthday, setBirthday] = useState(update.field_updates.birthday || '')
  const [nickname, setNickname] = useState(update.field_updates.nickname || '')
  const [notesToAppend, setNotesToAppend] = useState(update.field_updates.notes_to_append || '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      field_updates: {
        ...(birthday ? { birthday } : {}),
        ...(nickname ? { nickname } : {}),
        ...(notesToAppend ? { notes_to_append: notesToAppend } : {}),
      },
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <User className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{update.matched_person_name || `"${update.match_value}"`}</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium mb-1">Birthday</label>
          <input
            type="date"
            value={birthday}
            onChange={(e) => setBirthday(e.target.value)}
            className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Nickname</label>
          <input
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium mb-1">Notes to Add</label>
        <textarea
          value={notesToAppend}
          onChange={(e) => setNotesToAppend(e.target.value)}
          className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[60px]"
        />
      </div>

      <p className="text-xs text-muted-foreground">
        Note: Anecdotes cannot be edited here. Remove this entry if the anecdotes are incorrect.
      </p>

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="p-1.5 rounded-md hover:bg-accent text-muted-foreground"
        >
          <X className="h-4 w-4" />
        </button>
        <button
          type="submit"
          className="p-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <Check className="h-4 w-4" />
        </button>
      </div>
    </form>
  )
}
