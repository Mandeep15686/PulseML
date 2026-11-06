import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { Dashboard } from './pages/Dashboard'
import { Models } from './pages/Models'
import { ModelDetail } from './pages/ModelDetail'
import { Alerts } from './pages/Alerts'
import { Upload } from './pages/Upload'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <div className="pt-14 min-h-screen">
        <Routes>
          <Route path="/"           element={<Dashboard />} />
          <Route path="/models"     element={<Models />} />
          <Route path="/models/:id" element={<ModelDetail />} />
          <Route path="/alerts"     element={<Alerts />} />
          <Route path="/upload"     element={<Upload />} />
          <Route path="*" element={
            <div className="flex items-center justify-center h-64 text-gray-500">
              404 — Page not found
            </div>
          }/>
        </Routes>
      </div>
    </BrowserRouter>
  )
}
