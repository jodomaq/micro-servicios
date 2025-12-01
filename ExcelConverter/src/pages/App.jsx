import React, { useMemo, useState } from 'react'
import Upload from './Upload'
import Pay from './Pay'
import GoogleLogin from '../components/GoogleLogin'
import Dashboard from '../components/Dashboard'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App(){
  const { user, loading } = useAuth()
  const [uploadId, setUploadId] = useState(null)
  const [step, setStep] = useState(1)
  const [orderId, setOrderId] = useState(null)
  const [showDashboard, setShowDashboard] = useState(false)

  const goUpload = () => {
    setStep(1)
    setShowDashboard(false)
  }
  
  const goPay = () => setStep(2)

  const reset = () => {
    setUploadId(null)
    setOrderId(null)
    setStep(1)
    setShowDashboard(false)
  }

  const toggleDashboard = () => {
    setShowDashboard(!showDashboard)
  }

  if (loading) {
    return <div className="container"><p>Cargando...</p></div>
  }

  return (
    <div className="container">
      <div className="header">
        <h2>Conversor de Estados de Cuenta a Excel</h2>
        <div className="header-actions">
          {user && (
            <button className="btn btn-secondary" onClick={toggleDashboard}>
              {showDashboard ? 'Volver al Conversor' : 'Mi Cuenta'}
            </button>
          )}
          <button className="btn" onClick={reset}>Reiniciar</button>
        </div>
      </div>

      {!user && (
        <div className="login-section">
          <p>Inicia sesión con Google para acceder a suscripciones o continúa con pago único</p>
          <GoogleLogin />
        </div>
      )}

      <div className="card">
        {showDashboard ? (
          <Dashboard />
        ) : (
          <>
            {step === 1 && (
              <Upload apiBase={API_BASE} onUploaded={(id)=>{ setUploadId(id); goPay(); }} />
            )}
            {step === 2 && (
              <Pay apiBase={API_BASE} uploadId={uploadId} onBack={goUpload} />
            )}
          </>
        )}
      </div>

      {!showDashboard && (
        <div className="footer">
          <p>1) Sube un PDF (máx 10 páginas). 2) Paga $20 MXN con PayPal o suscríbete. 3) Descarga tu Excel.</p>
          {user && <p className="user-greeting">¡Hola, {user.name}! 👋</p>}
        </div>
      )}
    </div>
  )
}
