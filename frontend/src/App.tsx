import { Routes, Route, Navigate } from 'react-router-dom'
import Studio from './pages/Studio'
import Export from './pages/Export'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/studio" replace />} />
      <Route path="/studio" element={<Studio />} />
      <Route path="/export/:sessionId" element={<Export />} />
    </Routes>
  )
}
