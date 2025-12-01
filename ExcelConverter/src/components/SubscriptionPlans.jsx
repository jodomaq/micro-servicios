import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const PLANS = [
  {
    type: 'basic',
    name: 'Básico',
    conversions: 200,
    price: 200,
    description: '200 conversiones mensuales'
  },
  {
    type: 'standard',
    name: 'Estándar',
    conversions: 400,
    price: 300,
    description: '400 conversiones mensuales'
  },
  {
    type: 'premium',
    name: 'Premium',
    conversions: 600,
    price: 350,
    description: '600 conversiones mensuales',
    popular: true
  }
]

export default function SubscriptionPlans({ onSubscribed }) {
  const { user, getAuthHeader } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubscribe = async (planType) => {
    if (!user) {
      alert('Debes iniciar sesión para suscribirte')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_BASE}/converter/subscription/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({ plan_type: planType })
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || 'Error al crear la suscripción')
      }

      const data = await res.json()
      
      // Save plan type to localStorage for return page
      localStorage.setItem('pending_plan_type', planType)
      
      // Get approval URL from PayPal data
      const approvalUrl = data.paypal_data?.links?.find(
        link => link.rel === 'approve'
      )?.href

      if (approvalUrl) {
        // Redirect to PayPal for approval
        window.location.href = approvalUrl
      } else {
        throw new Error('No se pudo obtener el enlace de aprobación de PayPal')
      }
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="subscription-plans">
      <h2>Planes de Suscripción Mensual</h2>
      <p className="plans-subtitle">Elige el plan que mejor se adapte a tus necesidades</p>
      
      {error && <div className="error">{error}</div>}
      
      <div className="plans-grid">
        {PLANS.map((plan) => (
          <div key={plan.type} className={`plan-card ${plan.popular ? 'popular' : ''}`}>
            {plan.popular && <div className="popular-badge">Más Popular</div>}
            <h3>{plan.name}</h3>
            <div className="plan-price">
              <span className="price">${plan.price}</span>
              <span className="currency">MXN/mes</span>
            </div>
            <div className="plan-conversions">
              <strong>{plan.conversions}</strong> conversiones
            </div>
            <p className="plan-description">{plan.description}</p>
            <div className="plan-features">
              <p>✓ Conversión ilimitada de páginas</p>
              <p>✓ Soporte prioritario</p>
              <p>✓ Sin cargos adicionales</p>
              <p>✓ Cancela cuando quieras</p>
            </div>
            <button 
              className="btn btn-primary"
              onClick={() => handleSubscribe(plan.type)}
              disabled={loading || !user}
            >
              {loading ? 'Procesando...' : 'Suscribirse'}
            </button>
            <p className="price-per-conversion">
              ~${(plan.price / plan.conversions).toFixed(2)} MXN por conversión
            </p>
          </div>
        ))}
      </div>
      
      {!user && (
        <div className="login-prompt">
          <p>⚠️ Debes iniciar sesión con Google para suscribirte</p>
        </div>
      )}
    </div>
  )
}
