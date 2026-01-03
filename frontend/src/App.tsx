import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { PeopleList } from '@/pages/PeopleList'
import { PersonDetail } from '@/pages/PersonDetail'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="people" element={<PeopleList />} />
        <Route path="people/:id" element={<PersonDetail />} />
      </Route>
    </Routes>
  )
}

export default App
