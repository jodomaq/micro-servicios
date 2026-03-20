/**
 * Dashboard App - Estadísticas y reportes
 */
import { useState } from 'react'
import { Routes, Route, Navigate, NavLink, useNavigate } from 'react-router-dom'
import DashboardHome from './pages/DashboardHome'
import CommitteesStats from './pages/CommitteesStats'
import AttendanceStats from './pages/AttendanceStats'
import MapPage from './pages/MapPage'
import LoginPage from './pages/LoginPage'

function Sidebar({ open, onClose }) {
  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-header">
        <h2>Dashboard</h2>
        <p style={{ fontSize: '0.75rem', opacity: 0.7 }}>Análisis y Reportes</p>
      </div>
      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={onClose}>
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
          Resumen
        </NavLink>
        <NavLink to="/committees" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={onClose}>
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
          Comités
        </NavLink>
        <NavLink to="/attendance" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={onClose}>
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>
          Asistencia
        </NavLink>
        <NavLink to="/map" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={onClose}>
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
          Mapa
        </NavLink>
      </nav>
      <div style={{ padding: '16px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <button className="btn btn-primary btn-block" onClick={() => {
          localStorage.removeItem('access_token')
          window.location.href = '/login'
        }} style={{ fontSize: '0.85rem' }}>
          Cerrar Sesión
        </button>
      </div>
    </aside>
  )
}

function ProtectedLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const token = localStorage.getItem('access_token')
  if (!token) return <Navigate to="/login" replace />

  return (
    <div className="app">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="main-content">
        <div className="header-bar">
          <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
          <div></div>
        </div>
        <Routes>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardHome />} />
          <Route path="committees" element={<CommitteesStats />} />
          <Route path="attendance" element={<AttendanceStats />} />
          <Route path="map" element={<MapPage />} />
        </Routes>
      </div>
      {sidebarOpen && <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', zIndex: 99 }} onClick={() => setSidebarOpen(false)} />}
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={<ProtectedLayout />} />
    </Routes>
  )
}
