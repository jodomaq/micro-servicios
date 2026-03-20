/**
 * Asistencia - App de registro de asistencia a eventos
 * 
 * Flujo:
 * 1. Usuario ingresa código de evento (o llega por URL con código)
 * 2. Se muestra info del evento
 * 3. Usuario llena formulario (nombre, email, teléfono)
 * 4. Se captura geolocalización automáticamente
 * 5. Se envía registro de asistencia
 */
import { useState, useEffect, useCallback } from 'react'
import api from './services/api'

// Stati della geolocalización
const GEO_STATUS = { IDLE: 'idle', LOADING: 'loading', OK: 'ok', ERROR: 'error' }

function useGeolocation() {
  const [position, setPosition] = useState(null)
  const [status, setStatus] = useState(GEO_STATUS.IDLE)
  const [error, setError] = useState(null)

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setStatus(GEO_STATUS.ERROR)
      setError('Geolocalización no disponible en este navegador')
      return
    }
    setStatus(GEO_STATUS.LOADING)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setStatus(GEO_STATUS.OK)
      },
      (err) => {
        setStatus(GEO_STATUS.ERROR)
        setError(err.code === 1 ? 'Permiso de ubicación denegado' : 'No se pudo obtener ubicación')
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    )
  }, [])

  return { position, status, error, requestLocation }
}

export default function App() {
  // Event code - can come from URL path param
  const [eventCode, setEventCode] = useState('')
  const [eventInfo, setEventInfo] = useState(null)
  const [loadingEvent, setLoadingEvent] = useState(false)
  const [eventError, setEventError] = useState(null)

  // Form
  const [form, setForm] = useState({ full_name: '', email: '', phone: '' })
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null) // 'success' | 'duplicate' | 'error'
  const [resultMsg, setResultMsg] = useState('')

  // Geolocation
  const { position, status: geoStatus, error: geoError, requestLocation } = useGeolocation()

  // Check URL for event code on mount
  useEffect(() => {
    const path = window.location.pathname
    const match = path.match(/^\/evento\/(.+)$/) || path.match(/^\/(.+)$/)
    if (match && match[1] && match[1] !== '') {
      const code = match[1]
      setEventCode(code)
      loadEvent(code)
    }
  }, [])

  // Start geolocation when event is loaded
  useEffect(() => {
    if (eventInfo && geoStatus === GEO_STATUS.IDLE) {
      requestLocation()
    }
  }, [eventInfo, geoStatus, requestLocation])

  async function loadEvent(code) {
    if (!code) return
    setLoadingEvent(true)
    setEventError(null)
    try {
      const { data } = await api.get(`/attendance/event-info/${code}`)
      setEventInfo(data)
    } catch (err) {
      setEventError(err.response?.status === 404 ? 'Evento no encontrado' : 'Error al buscar evento')
      setEventInfo(null)
    } finally {
      setLoadingEvent(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.full_name || !form.email) return

    setSubmitting(true)
    setResult(null)
    try {
      const payload = {
        full_name: form.full_name,
        email: form.email,
        phone: form.phone || null,
        auth_provider: 'dev',
        latitude: position?.lat || null,
        longitude: position?.lng || null,
      }
      await api.post(`/attendance/register/${eventCode}`, payload)
      setResult('success')
      setResultMsg('¡Asistencia registrada exitosamente!')
    } catch (err) {
      const detail = err.response?.data?.detail || ''
      if (detail.toLowerCase().includes('ya registr') || err.response?.status === 409) {
        setResult('duplicate')
        setResultMsg('Ya te registraste a este evento anteriormente.')
      } else {
        setResult('error')
        setResultMsg(detail || 'Error al registrar asistencia')
      }
    } finally {
      setSubmitting(false)
    }
  }

  function handleChange(field) {
    return (e) => setForm(prev => ({ ...prev, [field]: e.target.value }))
  }

  // ============ RENDER ============

  // Success state
  if (result === 'success') {
    return (
      <div className="app">
        <div className="header">
          <h1>Asistencia</h1>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div className="success-check">✅</div>
          <h2 style={{ color: '#2e7d32', marginBottom: 8 }}>¡Registro Exitoso!</h2>
          <p style={{ marginBottom: 16 }}>{resultMsg}</p>
          <p style={{ color: '#999', fontSize: '0.85rem' }}>
            {eventInfo?.name}
          </p>
        </div>
        <div className="footer">Sistema de Asistencia Electoral</div>
      </div>
    )
  }

  return (
    <div className="app">
      <div className="header">
        <h1>📋 Registro de Asistencia</h1>
        <p>Ingresa el código del evento para registrarte</p>
      </div>

      {/* Event Code Input */}
      {!eventInfo && (
        <div className="card">
          <h2>Código de Evento</h2>
          <div className="code-input-wrapper">
            <input
              type="text"
              placeholder="Ej: 1-5"
              value={eventCode}
              onChange={(e) => setEventCode(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadEvent(eventCode)}
            />
            <button
              className="btn btn-primary"
              onClick={() => loadEvent(eventCode)}
              disabled={!eventCode || loadingEvent}
            >
              {loadingEvent ? '...' : 'Buscar'}
            </button>
          </div>
          {eventError && (
            <div className="alert alert-error" style={{ marginTop: 12 }}>{eventError}</div>
          )}
        </div>
      )}

      {/* Event Info */}
      {eventInfo && (
        <div className="card event-info">
          <div className="event-name">{eventInfo.name}</div>
          {eventInfo.description && (
            <div className="event-detail">{eventInfo.description}</div>
          )}
          {eventInfo.location && (
            <div className="event-detail">📍 {eventInfo.location}</div>
          )}
          {eventInfo.event_date && (
            <div className="event-detail">
              📅 {new Date(eventInfo.event_date).toLocaleDateString('es-MX', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
              })}
            </div>
          )}
        </div>
      )}

      {/* Duplicate alert */}
      {result === 'duplicate' && (
        <div className="alert alert-error">{resultMsg}</div>
      )}
      {result === 'error' && (
        <div className="alert alert-error">{resultMsg}</div>
      )}

      {/* Registration Form */}
      {eventInfo && result !== 'success' && (
        <div className="card">
          <h2>Tus Datos</h2>

          {/* Location status */}
          <div className={`location-status ${geoStatus === GEO_STATUS.OK ? 'ok' : geoStatus === GEO_STATUS.ERROR ? 'error' : 'pending'}`}>
            <div className={`location-dot ${geoStatus === GEO_STATUS.OK ? 'ok' : geoStatus === GEO_STATUS.ERROR ? 'error' : 'pending'}`}></div>
            {geoStatus === GEO_STATUS.LOADING && 'Obteniendo ubicación...'}
            {geoStatus === GEO_STATUS.OK && `Ubicación capturada (${position.lat.toFixed(4)}, ${position.lng.toFixed(4)})`}
            {geoStatus === GEO_STATUS.ERROR && (geoError || 'Ubicación no disponible')}
            {geoStatus === GEO_STATUS.IDLE && 'Esperando ubicación...'}
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Nombre completo *</label>
              <input
                type="text"
                value={form.full_name}
                onChange={handleChange('full_name')}
                placeholder="Tu nombre completo"
                required
              />
            </div>

            <div className="form-group">
              <label>Correo electrónico *</label>
              <input
                type="email"
                value={form.email}
                onChange={handleChange('email')}
                placeholder="tu@email.com"
                required
              />
            </div>

            <div className="form-group">
              <label>Teléfono (opcional)</label>
              <input
                type="tel"
                value={form.phone}
                onChange={handleChange('phone')}
                placeholder="10 dígitos"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || !form.full_name || !form.email}
            >
              {submitting ? (
                <><span className="spinner-inline"></span>Registrando...</>
              ) : (
                'Registrar Asistencia'
              )}
            </button>
          </form>
        </div>
      )}

      <div className="footer">Sistema de Asistencia Electoral</div>
    </div>
  )
}
