import { Routes, Route } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { PeopleList } from '@/pages/PeopleList'
import { PersonDetail } from '@/pages/PersonDetail'
import { TagsPage } from '@/pages/TagsPage'
import { GroupsPage } from '@/pages/GroupsPage'
import { AnecdotesPage } from '@/pages/AnecdotesPage'
import { PhotosPage } from '@/pages/PhotosPage'
import { RelationshipsPage } from '@/pages/RelationshipsPage'
import { GraphPage } from '@/pages/GraphPage'
import { MyProfile } from '@/pages/MyProfile'
import { ChatPage } from '@/pages/ChatPage'
import { SmartSearchPage } from '@/pages/SmartSearchPage'
import { ExportPage } from '@/pages/ExportPage'
import MFAVerify from '@/components/MFAVerify'
import { getAuthStatus } from '@/services/api'
import { Loader2 } from 'lucide-react'

function App() {
  const {
    data: authStatus,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['authStatus'],
    queryFn: getAuthStatus,
    staleTime: 30000, // 30 seconds
    retry: 1,
  })

  // Show loading spinner while checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  // Show error if auth check failed (don't redirect to avoid loops)
  if (isError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md p-6">
          <p className="text-red-600 mb-4">Failed to check authentication status</p>
          <p className="text-gray-600 text-sm mb-4">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // If not authenticated, redirect to login
  if (!authStatus?.authenticated) {
    // Redirect to Django login (proxied through Vite in dev)
    const loginUrl = `/accounts/login/?next=/`
    window.location.href = loginUrl
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-gray-600">Redirecting to login...</p>
        </div>
      </div>
    )
  }

  // If MFA is required but not verified, show MFA verification
  if (authStatus.mfa_required) {
    return <MFAVerify onSuccess={() => refetch()} />
  }

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="search" element={<SmartSearchPage />} />
        <Route path="people" element={<PeopleList />} />
        <Route path="people/:id" element={<PersonDetail />} />
        <Route path="relationships" element={<RelationshipsPage />} />
        <Route path="graph" element={<GraphPage />} />
        <Route path="anecdotes" element={<AnecdotesPage />} />
        <Route path="photos" element={<PhotosPage />} />
        <Route path="groups" element={<GroupsPage />} />
        <Route path="tags" element={<TagsPage />} />
        <Route path="export" element={<ExportPage />} />
        <Route path="me" element={<MyProfile />} />
      </Route>
    </Routes>
  )
}

export default App
