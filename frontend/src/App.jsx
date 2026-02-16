// src/App.jsx
import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Chatbot   from './pages/Chatbot'
import History   from './pages/History'
import Updates   from './pages/Updates'
import Layout    from './components/Layout'

export default function App() {
  const [userId, setUserId] = useState(() => localStorage.getItem('userId') || null)

  const handleLogin = (id) => {
    localStorage.setItem('userId', id)
    setUserId(id)
  }
  const handleLogout = () => {
    localStorage.removeItem('userId')
    setUserId(null)
  }

  if (!userId) {
    return <Onboarding onSuccess={handleLogin} />
  }

  return (
    <Layout userId={userId} onLogout={handleLogout}>
      <Routes>
        <Route path="/"         element={<Dashboard userId={userId} />} />
        <Route path="/updates"  element={<Updates   userId={userId} />} />
        <Route path="/chat"     element={<Chatbot   userId={userId} />} />
        <Route path="/history"  element={<History   userId={userId} />} />
        <Route path="*"         element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
