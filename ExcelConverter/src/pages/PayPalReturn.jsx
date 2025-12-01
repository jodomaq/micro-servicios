import React, { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function PayPalReturn() {
  const { getAuthHeader } = useAuth()
  const [status, setStatus] = useState('Procesando suscripción...')
  const [error, setError] = useState(null)

  useEffect(() => {
    handlePayPalReturn()
  }, [])

  const handlePayPalReturn = async () => {
    // Get URL parameters
    const params = new URLSearchParams(window.location.search)
    const subscriptionId = params.get('subscription_id') || params.get('token')
    const planType = params.get('plan_type') || localStorage.getItem('pending_plan_type')

    if (!subscriptionId) {
      setError('No se encontró el ID de suscripción')
      return
    }

    if (!planType) {
      setError('No se encontró el tipo de plan')
      return
    }

    try {
      const res = await fetch(`${API_BASE}/converter/subscription/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({
          subscription_id: subscriptionId,
          plan_type: planType
        })
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || 'Error al aprobar la suscripción')
      }

      const data = await res.json()
      setStatus('¡Suscripción activada exitosamente!')
      
      // Clean up
      localStorage.removeItem('pending_plan_type')
      
      // Redirect after 2 seconds
      setTimeout(() => {
        window.location.href = '/'
      }, 2000)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h2>Procesando Suscripción</h2>
        {error ? (
          <div>
            <p className="error">Error: {error}</p>
            <button className="btn" onClick={() => window.location.href = '/'}>
              Volver al inicio
            </button>
          </div>
        ) : (
          <p className="success">{status}</p>
        )}
      </div>
    </div>
  )
}
