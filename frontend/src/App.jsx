import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Questionnaire from './pages/Questionnaire'
import Dashboard from './pages/Dashboard'
import Supplements from './pages/Supplements'
import WearableDashboard from './pages/WearableDashboard'
import ChatAssistant from './components/ChatAssistant'

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/questionnaire" element={<Questionnaire />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/supplements" element={<Supplements />} />
          <Route path="/health/watch/:eventId" element={<WearableDashboard />} />
        </Routes>
      </main>
      <ChatAssistant />
      <Footer />
    </div>
  )
}
