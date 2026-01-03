import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from './Modal'
import { parseContactsWithAI, bulkImportContacts, type ParsedPerson } from '@/services/api'
import { Sparkles, Trash2, Edit2, Check, X, Loader2 } from 'lucide-react'

interface AIImportModalProps {
  isOpen: boolean
  onClose: () => void
}

type Step = 'input' | 'preview' | 'result'

export function AIImportModal({ isOpen, onClose }: AIImportModalProps) {
  const queryClient = useQueryClient()
  const [step, setStep] = useState<Step>('input')
  const [inputText, setInputText] = useState('')
  const [parsedPersons, setParsedPersons] = useState<ParsedPerson[]>([])
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [importResult, setImportResult] = useState<{
    persons_created: number
    relationships_created: number
    errors: string[]
  } | null>(null)

  const parseMutation = useMutation({
    mutationFn: parseContactsWithAI,
    onSuccess: (data) => {
      setParsedPersons(data.persons)
      setStep('preview')
    },
  })

  const importMutation = useMutation({
    mutationFn: bulkImportContacts,
    onSuccess: (data) => {
      setImportResult({
        persons_created: data.summary.persons_created,
        relationships_created: data.summary.relationships_created,
        errors: data.errors,
      })
      setStep('result')
      queryClient.invalidateQueries({ queryKey: ['persons'] })
      queryClient.invalidateQueries({ queryKey: ['relationships'] })
    },
  })

  const handleClose = () => {
    setStep('input')
    setInputText('')
    setParsedPersons([])
    setEditingIndex(null)
    setImportResult(null)
    onClose()
  }

  const handleParse = () => {
    if (!inputText.trim()) return
    parseMutation.mutate(inputText)
  }

  const handleImport = () => {
    if (parsedPersons.length === 0) return
    importMutation.mutate(parsedPersons)
  }

  const handleRemovePerson = (index: number) => {
    setParsedPersons((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpdatePerson = (index: number, updates: Partial<ParsedPerson>) => {
    setParsedPersons((prev) =>
      prev.map((person, i) => (i === index ? { ...person, ...updates } : person))
    )
  }

  const exampleText = `My mother is Marie Dupont, born on March 15, 1960. She works as a teacher.
My brother is Pierre Dupont, born in 1985. He lives in Paris and works as an engineer.
My best friend is Sophie Martin, we met in college. Her birthday is July 22nd.`

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={
        step === 'input'
          ? 'AI Import Contacts'
          : step === 'preview'
            ? 'Review & Import'
            : 'Import Complete'
      }
      size="xl"
    >
      {step === 'input' && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 bg-primary/5 border border-primary/20 rounded-lg">
            <Sparkles className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-primary">AI-Powered Import</p>
              <p className="text-muted-foreground mt-1">
                Describe your contacts in natural language. Include names, relationships (mother,
                father, friend, etc.), birthdays, and any notes. The AI will parse and structure
                the information for you.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Describe your contacts
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[200px]"
              placeholder={exampleText}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Tip: Include relationship types like mother, father, sister, brother, friend, colleague, etc.
            </p>
          </div>

          {parseMutation.error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
              {(parseMutation.error as Error).message || 'Failed to parse contacts. Please try again.'}
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
                  Parsing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Parse with AI
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {step === 'preview' && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Review the parsed contacts below. You can edit or remove entries before importing.
          </p>

          {parsedPersons.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground border rounded-lg">
              No contacts were found in the text. Please try again with more details.
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {parsedPersons.map((person, index) => (
                <div
                  key={index}
                  className="p-4 border rounded-lg bg-card"
                >
                  {editingIndex === index ? (
                    <EditPersonForm
                      person={person}
                      onSave={(updates) => {
                        handleUpdatePerson(index, updates)
                        setEditingIndex(null)
                      }}
                      onCancel={() => setEditingIndex(null)}
                    />
                  ) : (
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {person.first_name} {person.last_name}
                          </span>
                          {person.relationship_to_owner && (
                            <span className="px-2 py-0.5 text-xs rounded-full bg-pink-100 text-pink-700 capitalize">
                              {person.relationship_to_owner}
                            </span>
                          )}
                        </div>
                        {person.nickname && (
                          <p className="text-sm text-muted-foreground">
                            Nickname: "{person.nickname}"
                          </p>
                        )}
                        {person.birthday && (
                          <p className="text-sm text-muted-foreground">
                            Birthday: {person.birthday}
                          </p>
                        )}
                        {person.notes && (
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {person.notes}
                          </p>
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
                          onClick={() => handleRemovePerson(index)}
                          className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                          title="Remove"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {importMutation.error && (
            <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
              {(importMutation.error as Error).message || 'Failed to import contacts. Please try again.'}
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
                onClick={handleImport}
                disabled={importMutation.isPending || parsedPersons.length === 0}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
              >
                {importMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>Import {parsedPersons.length} Contact{parsedPersons.length !== 1 ? 's' : ''}</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {step === 'result' && importResult && (
        <div className="space-y-4">
          <div className="p-6 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
              <Check className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold">Import Complete!</h3>
            <p className="text-muted-foreground mt-1">
              Successfully imported {importResult.persons_created} contact
              {importResult.persons_created !== 1 ? 's' : ''}
              {importResult.relationships_created > 0 && (
                <> with {importResult.relationships_created} relationship
                {importResult.relationships_created !== 1 ? 's' : ''}</>
              )}
            </p>
          </div>

          {importResult.errors.length > 0 && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="font-medium text-yellow-800 text-sm">Some issues occurred:</p>
              <ul className="mt-2 space-y-1 text-sm text-yellow-700">
                {importResult.errors.map((error, i) => (
                  <li key={i}>• {error}</li>
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

interface EditPersonFormProps {
  person: ParsedPerson
  onSave: (updates: Partial<ParsedPerson>) => void
  onCancel: () => void
}

function EditPersonForm({ person, onSave, onCancel }: EditPersonFormProps) {
  const [firstName, setFirstName] = useState(person.first_name)
  const [lastName, setLastName] = useState(person.last_name)
  const [nickname, setNickname] = useState(person.nickname)
  const [birthday, setBirthday] = useState(person.birthday || '')
  const [notes, setNotes] = useState(person.notes)
  const [relationship, setRelationship] = useState(person.relationship_to_owner)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      first_name: firstName,
      last_name: lastName,
      nickname,
      birthday: birthday || null,
      notes,
      relationship_to_owner: relationship,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium mb-1">First Name</label>
          <input
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
            className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Last Name</label>
          <input
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium mb-1">Nickname</label>
          <input
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div>
          <label className="block text-xs font-medium mb-1">Birthday</label>
          <input
            type="date"
            value={birthday}
            onChange={(e) => setBirthday(e.target.value)}
            className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium mb-1">Relationship to You</label>
        <input
          type="text"
          value={relationship}
          onChange={(e) => setRelationship(e.target.value)}
          placeholder="e.g., mother, friend, colleague"
          className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div>
        <label className="block text-xs font-medium mb-1">Notes</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="w-full px-2 py-1.5 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[60px]"
        />
      </div>
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
