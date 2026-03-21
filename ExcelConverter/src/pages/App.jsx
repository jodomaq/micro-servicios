import React, { useState } from 'react'
import Upload from './Upload'
import Pay from './Pay'
import GoogleLogin from '../components/GoogleLogin'
import Dashboard from '../components/Dashboard'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const { user, loading } = useAuth()
  const [uploadId, setUploadId] = useState(null)
  const [step, setStep] = useState(1)
  const [showDashboard, setShowDashboard] = useState(false)

  const goUpload = () => { setStep(1); setShowDashboard(false) }
  const goPay   = () => setStep(2)

  const reset = () => {
    setUploadId(null)
    setStep(1)
    setShowDashboard(false)
  }

  if (loading) {
    return (
      <div className="ms-page" style={{ display:'flex', alignItems:'center', justifyContent:'center', minHeight:'100vh' }}>
        <div className="ms-spinner" style={{ width:'2rem', height:'2rem' }}></div>
      </div>
    )
  }

  return (
    <div className="ms-page">
      {/* Navbar */}
      <nav className="ms-nav">
        <a href="/" className="ms-nav__logo">Micro-Servicios</a>
        <ul className="ms-nav__links">
          <li><a href="/" className="ms-nav__link">Inicio</a></li>
          <li><a href="#" className="ms-nav__link active">Conversor PDF</a></li>
        </ul>
        <div style={{ display:'flex', gap:'var(--ms-space-3)', alignItems:'center', marginLeft:'auto' }}>
          {user ? (
            <>
              <button
                className="ms-btn ms-btn--ghost ms-btn--sm"
                onClick={() => setShowDashboard(!showDashboard)}
              >
                {showDashboard ? 'Volver al Conversor' : 'Mi Cuenta'}
              </button>
              <div className="ms-avatar" title={user.name}>
                {user.picture
                  ? <img src={user.picture} alt={user.name} style={{ width:'100%', height:'100%', borderRadius:'50%', objectFit:'cover' }} />
                  : user.name?.[0]?.toUpperCase()}
              </div>
            </>
          ) : (
            <GoogleLogin />
          )}
        </div>
      </nav>

      <div className="container">
        {/* Hero — solo si no está en dashboard */}
        {!showDashboard && step === 1 && (
          <div style={{ textAlign:'center', padding:'var(--ms-space-12) 0 var(--ms-space-8)' }}>
            <h1 style={{
              fontSize:'var(--ms-text-4xl)',
              fontWeight:800,
              color:'var(--ms-text-white)',
              margin:'0 0 var(--ms-space-4) 0',
              lineHeight:1.2
            }}>
              Convierte tus<br/>
              <span style={{ background:'var(--ms-gradient-brand)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent', backgroundClip:'text' }}>
                Estados de Cuenta
              </span>{' '}a Excel
            </h1>
            <p style={{ color:'var(--ms-text-muted)', fontSize:'var(--ms-text-lg)', maxWidth:520, margin:'0 auto var(--ms-space-6)' }}>
              Sube tu PDF, paga $20 MXN o suscríbete, y descarga tu archivo Excel listo para usar.
            </p>
          </div>
        )}

        {/* Indicador de pasos */}
        {!showDashboard && (
          <div style={{
            display:'flex',
            gap:'var(--ms-space-4)',
            justifyContent:'center',
            marginBottom:'var(--ms-space-6)',
            flexWrap:'wrap'
          }}>
            {['Sube tu PDF', 'Paga', 'Descarga'].map((label, i) => (
              <div key={i} style={{
                display:'flex',
                alignItems:'center',
                gap:'var(--ms-space-2)',
                opacity: step - 1 === i ? 1 : 0.45
              }}>
                <div style={{
                  width:'1.75rem', height:'1.75rem', borderRadius:'50%',
                  background: step - 1 === i ? 'var(--ms-gradient-brand)' : 'var(--ms-bg-dark3)',
                  border: step - 1 === i ? 'none' : '1px solid rgba(255,255,255,0.15)',
                  display:'flex', alignItems:'center', justifyContent:'center',
                  fontSize:'var(--ms-text-xs)', fontWeight:700, color:'var(--ms-text-white)', flexShrink:0
                }}>
                  {i + 1}
                </div>
                <span style={{ fontSize:'var(--ms-text-sm)', color: step - 1 === i ? 'var(--ms-text-white)' : 'var(--ms-text-muted)', fontWeight: step - 1 === i ? 600 : 400 }}>
                  {label}
                </span>
                {i < 2 && (
                  <div style={{ width:32, height:1, background:'rgba(255,255,255,0.1)', marginLeft:'var(--ms-space-2)' }}/>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Contenido principal */}
        <div className="card">
          {showDashboard ? (
            <Dashboard />
          ) : (
            <>
              {step === 1 && (
                <Upload apiBase={API_BASE} onUploaded={(id) => { setUploadId(id); goPay() }} />
              )}
              {step === 2 && (
                <Pay apiBase={API_BASE} uploadId={uploadId} onBack={goUpload} />
              )}
            </>
          )}
        </div>

        <div className="footer">
          <p>Formatos soportados: estados de cuenta bancarios en PDF · Máx. 10 páginas · Pago seguro con PayPal</p>
          {user && <p className="user-greeting">Hola, {user.name}</p>}
        </div>
      </div>
    </div>
  )
}
