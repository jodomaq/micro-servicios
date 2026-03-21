import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const PLANS = [
  { type: 'basic',    name: 'Básico',    conversions: 200, price: 200 },
  { type: 'standard', name: 'Estándar',  conversions: 400, price: 300 },
  { type: 'premium',  name: 'Premium',   conversions: 600, price: 350, popular: true },
]

export default function SubscriptionPlans() {
  const { user, getAuthHeader } = useAuth()
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  const handleSubscribe = async (planType) => {
    if (!user) { setError('Debes iniciar sesión para suscribirte.'); return }
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/converter/subscription/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify({ plan_type: planType })
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail || 'Error al crear la suscripción.')
      }
      const data = await res.json()
      localStorage.setItem('pending_plan_type', planType)
      const approvalUrl = data.paypal_data?.links?.find(l => l.rel === 'approve')?.href
      if (!approvalUrl) throw new Error('No se pudo obtener el enlace de PayPal.')
      window.location.href = approvalUrl
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="subscription-plans">
      <h2 style={{ color:'var(--ms-text-white)', margin:'0 0 var(--ms-space-2) 0' }}>Planes de Suscripción</h2>
      <p className="plans-subtitle">Más conversiones, mejor precio por unidad</p>

      {error && <div className="status-msg error" style={{ marginBottom:'var(--ms-space-4)' }}>{error}</div>}

      <div className="plans-grid">
        {PLANS.map((plan) => (
          <div key={plan.type} className={`plan-card ${plan.popular ? 'popular' : ''}`}>
            {plan.popular && <div className="popular-badge">Más popular</div>}
            <h3>{plan.name}</h3>
            <div className="plan-price">
              <span className="price">${plan.price}</span>
              <span className="currency">MXN/mes</span>
            </div>
            <div className="plan-conversions">
              <strong>{plan.conversions}</strong> conversiones
            </div>
            <div className="plan-features">
              <p>✓ Conversión de PDFs ilimitada</p>
              <p>✓ Historial de conversiones</p>
              <p>✓ Soporte prioritario</p>
              <p>✓ Cancela en cualquier momento</p>
            </div>
            <button
              className="btn btn-primary"
              style={{ width:'100%' }}
              onClick={() => handleSubscribe(plan.type)}
              disabled={loading || !user}
            >
              {loading ? <><span className="ms-spinner"></span> Procesando...</> : 'Suscribirse'}
            </button>
            <p className="price-per-conversion">
              ~${(plan.price / plan.conversions).toFixed(2)} MXN por conversión
            </p>
          </div>
        ))}
      </div>

      {!user && (
        <div className="login-prompt">
          Inicia sesión con Google para suscribirte
        </div>
      )}
    </div>
  )
}
