import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function Dashboard() {
  const { user, logout, getAuthHeader } = useAuth()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState('')

  useEffect(() => { loadDashboard() }, [])

  const loadDashboard = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/subscriptions/dashboard`, { headers: getAuthHeader() })
      if (!res.ok) throw new Error('Error al cargar el panel de control.')
      setDashboard(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const cancelSubscription = async () => {
    if (!dashboard?.active_subscription) return
    if (!confirm('¿Cancelar tu suscripción activa?')) return
    try {
      const res = await fetch(
        `${API_BASE}/subscriptions/${dashboard.active_subscription.id}`,
        { method: 'DELETE', headers: getAuthHeader() }
      )
      if (!res.ok) throw new Error('No se pudo cancelar.')
      loadDashboard()
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="ms-spinner" style={{ width:'2rem', height:'2rem' }}></div>
        <span style={{ color:'var(--ms-text-muted)' }}>Cargando tu cuenta...</span>
      </div>
    )
  }

  if (error) {
    return <div className="status-msg error">{error}</div>
  }

  const sub = dashboard?.active_subscription

  return (
    <div className="dashboard">
      {/* Perfil */}
      <div className="user-info">
        <div className="user-header">
          {user?.picture
            ? <img src={user.picture} alt={user.name} className="user-avatar" />
            : <div className="ms-avatar">{user?.name?.[0]?.toUpperCase()}</div>
          }
          <div>
            <h3>{user?.name}</h3>
            <p>{user?.email}</p>
          </div>
        </div>
        <button className="btn btn-secondary" onClick={logout}>Cerrar sesión</button>
      </div>

      {/* Suscripción */}
      {sub ? (
        <div className="subscription-info">
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'var(--ms-space-3)', marginBottom:'var(--ms-space-4)' }}>
            <h3 style={{ margin:0 }}>Suscripción activa</h3>
            <span className="ms-badge ms-badge--success">Activa</span>
          </div>
          <div className="subscription-details">
            <p><strong>Plan:</strong> {getPlanName(sub.plan_type)}</p>
            <p><strong>Precio:</strong> ${sub.price} {sub.currency}/mes</p>
            <p>
              <strong>Conversiones:</strong>{' '}
              {sub.conversions_used} / {sub.conversions_limit}{' '}
              <span className="ms-badge ms-badge--primary" style={{ marginLeft:'var(--ms-space-2)' }}>
                {dashboard.conversions_remaining} restantes
              </span>
            </p>
            <p><strong>Válido hasta:</strong> {new Date(sub.end_date).toLocaleDateString('es-MX')}</p>
          </div>
          <button className="btn btn-danger ms-btn--sm" onClick={cancelSubscription}>
            Cancelar suscripción
          </button>
        </div>
      ) : (
        <div className="no-subscription">
          <h3>Sin suscripción activa</h3>
          <p>Puedes pagar por conversión única ($20 MXN) o suscribirte para obtener hasta 600 conversiones mensuales.</p>
        </div>
      )}

      {/* Estadísticas */}
      <div className="stats">
        <h3>Estadísticas</h3>
        <p>
          <strong>Total de conversiones realizadas:</strong>{' '}
          <span className="ms-badge ms-badge--primary">{dashboard?.total_conversions || 0}</span>
        </p>
      </div>

      {/* Conversiones recientes */}
      {dashboard?.recent_conversions?.length > 0 && (
        <div className="recent-conversions">
          <h3>Conversiones recientes</h3>
          <ul>
            {dashboard.recent_conversions.map((conv) => (
              <li key={conv.id}>
                <span style={{ fontWeight:500, color:'var(--ms-text-white)' }}>
                  {conv.filename || 'Sin nombre'}
                </span>
                <span>{new Date(conv.created_at).toLocaleDateString('es-MX')}</span>
                <span className={`ms-badge ${conv.success ? 'ms-badge--success' : 'ms-badge--danger'}`}>
                  {conv.success ? '✓ Exitosa' : '✗ Fallida'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && <div className="status-msg error">{error}</div>}
    </div>
  )
}

function getPlanName(planType) {
  return { basic: 'Básico (200)', standard: 'Estándar (400)', premium: 'Premium (600)' }[planType] ?? planType
}
