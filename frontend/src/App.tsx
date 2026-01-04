import { Routes, Route } from 'react-router-dom'
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

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="people" element={<PeopleList />} />
        <Route path="people/:id" element={<PersonDetail />} />
        <Route path="relationships" element={<RelationshipsPage />} />
        <Route path="graph" element={<GraphPage />} />
        <Route path="anecdotes" element={<AnecdotesPage />} />
        <Route path="photos" element={<PhotosPage />} />
        <Route path="groups" element={<GroupsPage />} />
        <Route path="tags" element={<TagsPage />} />
        <Route path="me" element={<MyProfile />} />
      </Route>
    </Routes>
  )
}

export default App
