import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { setupMFA, confirmMFA, disableMFA } from '@/services/api'
import type { MFASetupResponse } from '@/types'
import { Modal } from './Modal'
import {
  ShieldCheck,
  ShieldOff,
  Loader2,
  Copy,
  Check,
  AlertTriangle,
} from 'lucide-react'

interface MFASetupProps {
  isEnabled: boolean
  onStatusChange?: () => void
}

export default function MFASetup({ isEnabled, onStatusChange }: MFASetupProps) {
  const [isSetupModalOpen, setIsSetupModalOpen] = useState(false)
  const [isDisableModalOpen, setIsDisableModalOpen] = useState(false)
  const [setupData, setSetupData] = useState<MFASetupResponse | null>(null)
  const [token, setToken] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [secretCopied, setSecretCopied] = useState(false)
  const queryClient = useQueryClient()

  const setupMutation = useMutation({
    mutationFn: setupMFA,
    onSuccess: (data) => {
      setSetupData(data)
      setError('')
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      setError(err.response?.data?.detail || 'Failed to start MFA setup')
    },
  })

  const confirmMutation = useMutation({
    mutationFn: confirmMFA,
    onSuccess: () => {
      setIsSetupModalOpen(false)
      setSetupData(null)
      setToken('')
      queryClient.invalidateQueries({ queryKey: ['mfaStatus'] })
      queryClient.invalidateQueries({ queryKey: ['authStatus'] })
      onStatusChange?.()
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      setError(err.response?.data?.detail || 'Invalid verification code')
    },
  })

  const disableMutation = useMutation({
    mutationFn: ({ token, password }: { token: string; password: string }) =>
      disableMFA(token, password),
    onSuccess: () => {
      setIsDisableModalOpen(false)
      setToken('')
      setPassword('')
      queryClient.invalidateQueries({ queryKey: ['mfaStatus'] })
      queryClient.invalidateQueries({ queryKey: ['authStatus'] })
      onStatusChange?.()
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      setError(err.response?.data?.detail || 'Failed to disable MFA')
    },
  })

  const handleStartSetup = () => {
    setError('')
    setSetupData(null)
    setToken('')
    setIsSetupModalOpen(true)
    setupMutation.mutate()
  }

  const handleConfirm = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (token.length !== 6 || !/^\d+$/.test(token)) {
      setError('Please enter a 6-digit code')
      return
    }

    confirmMutation.mutate(token)
  }

  const handleDisable = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (token.length !== 6 || !/^\d+$/.test(token)) {
      setError('Please enter a 6-digit code')
      return
    }

    if (!password) {
      setError('Please enter your password')
      return
    }

    disableMutation.mutate({ token, password })
  }

  const copySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret)
      setSecretCopied(true)
      setTimeout(() => setSecretCopied(false), 2000)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isEnabled ? (
            <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
              <ShieldCheck className="h-6 w-6 text-green-600" />
            </div>
          ) : (
            <div className="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center">
              <ShieldOff className="h-6 w-6 text-yellow-600" />
            </div>
          )}
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Two-Factor Authentication
            </h3>
            <p className="text-sm text-gray-500">
              {isEnabled
                ? 'Your account is protected with 2FA'
                : 'Add an extra layer of security to your account'}
            </p>
          </div>
        </div>

        {isEnabled ? (
          <button
            onClick={() => {
              setError('')
              setToken('')
              setPassword('')
              setIsDisableModalOpen(true)
            }}
            className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100"
          >
            Disable 2FA
          </button>
        ) : (
          <button
            onClick={handleStartSetup}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
          >
            Enable 2FA
          </button>
        )}
      </div>

      {/* Setup Modal */}
      <Modal
        isOpen={isSetupModalOpen}
        onClose={() => {
          setIsSetupModalOpen(false)
          setSetupData(null)
          setToken('')
          setError('')
        }}
        title="Set Up Two-Factor Authentication"
      >
        <div className="space-y-6">
          {setupMutation.isPending && !setupData && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
          )}

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {setupData && (
            <>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-4">
                  Scan this QR code with your authenticator app:
                </p>
                <img
                  src={setupData.qr_code}
                  alt="MFA QR Code"
                  className="mx-auto w-48 h-48"
                />
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-2">
                  Or enter this secret manually:
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-sm font-mono bg-white px-3 py-2 rounded border break-all">
                    {setupData.secret}
                  </code>
                  <button
                    onClick={copySecret}
                    className="p-2 text-gray-500 hover:text-gray-700"
                    title="Copy secret"
                  >
                    {secretCopied ? (
                      <Check className="h-5 w-5 text-green-600" />
                    ) : (
                      <Copy className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              <form onSubmit={handleConfirm} className="space-y-4">
                <div>
                  <label
                    htmlFor="setup-token"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Enter the 6-digit code from your app:
                  </label>
                  <input
                    id="setup-token"
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={6}
                    value={token}
                    onChange={(e) => setToken(e.target.value.replace(/\D/g, ''))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg text-center text-xl tracking-widest focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="000000"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setIsSetupModalOpen(false)
                      setSetupData(null)
                      setToken('')
                    }}
                    className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={confirmMutation.isPending || token.length !== 6}
                    className="flex-1 flex justify-center items-center gap-2 py-2 px-4 border border-transparent rounded-lg text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {confirmMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Verifying...
                      </>
                    ) : (
                      'Confirm Setup'
                    )}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </Modal>

      {/* Disable Modal */}
      <Modal
        isOpen={isDisableModalOpen}
        onClose={() => {
          setIsDisableModalOpen(false)
          setToken('')
          setPassword('')
          setError('')
        }}
        title="Disable Two-Factor Authentication"
      >
        <div className="space-y-6">
          <div className="flex items-center gap-3 p-4 bg-yellow-50 rounded-lg">
            <AlertTriangle className="h-6 w-6 text-yellow-600 flex-shrink-0" />
            <p className="text-sm text-yellow-800">
              Disabling 2FA will make your account less secure. You'll be able
              to enable it again at any time.
            </p>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleDisable} className="space-y-4">
            <div>
              <label
                htmlFor="disable-token"
                className="block text-sm font-medium text-gray-700"
              >
                Verification Code
              </label>
              <input
                id="disable-token"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                value={token}
                onChange={(e) => setToken(e.target.value.replace(/\D/g, ''))}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg text-center text-xl tracking-widest focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="000000"
              />
            </div>

            <div>
              <label
                htmlFor="disable-password"
                className="block text-sm font-medium text-gray-700"
              >
                Current Password
              </label>
              <input
                id="disable-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setIsDisableModalOpen(false)
                  setToken('')
                  setPassword('')
                }}
                className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={
                  disableMutation.isPending || token.length !== 6 || !password
                }
                className="flex-1 flex justify-center items-center gap-2 py-2 px-4 border border-transparent rounded-lg text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {disableMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Disabling...
                  </>
                ) : (
                  'Disable 2FA'
                )}
              </button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  )
}
