import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { verifyMFA } from '@/services/api'
import { ShieldCheck, Loader2 } from 'lucide-react'

interface MFAVerifyProps {
  onSuccess: () => void
  onCancel?: () => void
}

export default function MFAVerify({ onSuccess, onCancel }: MFAVerifyProps) {
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const queryClient = useQueryClient()

  const verifyMutation = useMutation({
    mutationFn: verifyMFA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['authStatus'] })
      onSuccess()
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      setError(err.response?.data?.detail || 'Invalid verification code')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (token.length !== 6 || !/^\d+$/.test(token)) {
      setError('Please enter a 6-digit code')
      return
    }

    verifyMutation.mutate(token)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-indigo-100">
            <ShieldCheck className="h-10 w-10 text-indigo-600" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Two-Factor Authentication
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Enter the 6-digit code from your authenticator app
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="token" className="sr-only">
              Verification Code
            </label>
            <input
              id="token"
              name="token"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              required
              maxLength={6}
              value={token}
              onChange={(e) => setToken(e.target.value.replace(/\D/g, ''))}
              className="appearance-none relative block w-full px-3 py-4 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg text-center text-2xl tracking-widest focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10"
              placeholder="000000"
              autoFocus
            />
          </div>

          <div className="flex gap-3">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={verifyMutation.isPending || token.length !== 6}
              className="flex-1 flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-lg text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {verifyMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Verify'
              )}
            </button>
          </div>
        </form>

        <p className="text-center text-xs text-gray-500">
          Open your authenticator app (Google Authenticator, Authy, etc.) to get
          the verification code.
        </p>
      </div>
    </div>
  )
}
