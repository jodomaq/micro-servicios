import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function Dashboard() {
  const { user, logout, getAuthHeader } = useAuth()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/subscriptions/dashboard`, {
        headers: getAuthHeader()
      })

      if (!res.ok) {
        throw new Error('Error al cargar el dashboard')
      }

      const data = await res.json()
      setDashboard(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const cancelSubscription = async () => {
    if (!dashboard?.active_subscription) return
    
    const confirmed = confirm('¿Estás seguro de que deseas cancelar tu suscripción?')
    if (!confirmed) return

    try {
      const res = await fetch(
        `${API_BASE}/subscriptions/${dashboard.active_subscription.id}`,
        {
          method: 'DELETE',
          headers: getAuthHeader()
        }
      )

      if (!res.ok) {
        throw new Error('Error al cancelar la suscripción')
      }

      alert('Suscripción cancelada exitosamente')
      loadDashboard()
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }

  if (loading) {
    return <div className="dashboard-loading">Cargando...</div>
  }

  if (error) {
    return <div className="error">Error: {error}</div>
  }

  const subscription = dashboard?.active_subscription
  const conversionsRemaining = dashboard?.conversions_remaining

  return (
    <div className="dashboard">
      <div className="user-info">
        <div className="user-header">
          {user?.picture && <img src={user.picture} alt={user.name} className="user-avatar" />}
          <div>
            <h3>{user?.name}</h3>
            <p>{user?.email}</p>
          </div>
        </div>
        <button className="btn btn-secondary" onClick={logout}>Cerrar sesión</button>
      </div>

      {subscription ? (
        <div className="subscription-info">
          <h3>Suscripción Activa</h3>
          <div className="subscription-details">
            <p><strong>Plan:</strong> {getPlanName(subscription.plan_type)}</p>
            <p><strong>Precio:</strong> ${subscription.price} {subscription.currency}/mes</p>
            <p><strong>Conversiones:</strong> {subscription.conversions_used} / {subscription.conversions_limit}</p>
            <p><strong>Conversiones restantes:</strong> {conversionsRemaining}</p>
            <p><strong>Válido hasta:</strong> {new Date(subscription.end_date).toLocaleDateString('es-MX')}</p>
          </div>
          <button className="btn btn-danger" onClick={cancelSubscription}>
            Cancelar Suscripción
          </button>
        </div>
      ) : (
        <div className="no-subscription">
          <p>No tienes una suscripción activa</p>
          <p>Puedes pagar por conversión única o suscribirte para obtener más conversiones a mejor precio</p>
        </div>
      )}

      <div className="stats">
        <h3>Estadísticas</h3>
        <p><strong>Total de conversiones:</strong> {dashboard?.total_conversions || 0}</p>
      </div>

      {dashboard?.recent_conversions && dashboard.recent_conversions.length > 0 && (
        <div className="recent-conversions">
          <h3>Conversiones Recientes</h3>
          <ul>
            {dashboard.recent_conversions.map((conv) => (
              <li key={conv.id}>
                <span>{conv.filename || 'Sin nombre'}</span>
                <span>{new Date(conv.created_at).toLocaleDateString('es-MX')}</span>
                <span className={conv.success ? 'success' : 'error'}>
                  {conv.success ? '✓ Exitosa' : '✗ Fallida'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function getPlanName(planType) {
  const names = {
    basic: 'Básico (200 conversiones)',
    standard: 'Estándar (400 conversiones)',
    premium: 'Premium (600 conversiones)'
  }
  return names[planType] || planType
}
