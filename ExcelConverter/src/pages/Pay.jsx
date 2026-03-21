import React, { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import SubscriptionPlans from '../components/SubscriptionPlans'

export default function Pay({ apiBase, uploadId, onBack }) {
  const { user, getAuthHeader } = useAuth()
  const [orderId, setOrderId]   = useState(null)
  const [approvalUrl, setApprovalUrl] = useState(null)
  const [status, setStatus]     = useState(null)   // { type, text }
  const [busy, setBusy]         = useState(false)
  const [paymentMode, setPaymentMode] = useState('onetime')
  const [conversionsLeft, setConversionsLeft] = useState(0)

  useEffect(() => {
    if (user) checkSubscription()
  }, [user])

  const checkSubscription = async () => {
    try {
      const res = await fetch(`${apiBase}/subscriptions/dashboard`, { headers: getAuthHeader() })
      if (res.ok) {
        const data = await res.json()
        setConversionsLeft(data.conversions_remaining ?? 0)
        if ((data.conversions_remaining ?? 0) > 0) {
          setStatus({ type: 'info', text: `Tienes ${data.conversions_remaining} conversión(es) disponibles en tu suscripción.` })
        }
      }
    } catch { /* silencioso */ }
  }

  const createOrder = async () => {
    setBusy(true)
    setStatus({ type: 'info', text: 'Creando orden en PayPal...' })
    try {
      const res = await fetch(`${apiBase}/converter/paypal/create-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error al crear la orden.' }))
        throw new Error(err.detail || 'Error al crear la orden.')
      }
      const data = await res.json()
      setOrderId(data.id)
      const link = (data.links || []).find(l => l.rel === 'approve' || l.rel === 'payer-action')?.href
      setApprovalUrl(link || null)
      setStatus({ type: 'success', text: 'Orden creada. Haz clic en "Pagar con PayPal" para completar el pago.' })
    } catch (e) {
      setStatus({ type: 'error', text: e.message })
    } finally {
      setBusy(false)
    }
  }

  const captureAndDownload = async () => {
    if (!orderId || !uploadId) return
    setBusy(true)
    setStatus({ type: 'info', text: 'Verificando pago y generando Excel...' })
    try {
      const res = await fetch(`${apiBase}/converter/paypal/capture-and-convert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify({ order_id: orderId, upload_id: uploadId })
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error al convertir el archivo.' }))
        throw new Error(err.detail || 'Error al convertir el archivo.')
      }
      triggerDownload(await res.blob())
      setStatus({ type: 'success', text: '¡Descarga iniciada! Tu archivo Excel está listo.' })
    } catch (e) {
      setStatus({ type: 'error', text: e.message })
    } finally {
      setBusy(false)
    }
  }

  const convertWithSubscription = async () => {
    if (!uploadId) { setStatus({ type: 'error', text: 'Primero sube tu archivo.' }); return }
    setBusy(true)
    setStatus({ type: 'info', text: 'Generando Excel con tu suscripción...' })
    try {
      const res = await fetch(`${apiBase}/converter/convert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify({ upload_id: uploadId })
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error al convertir el archivo.' }))
        throw new Error(err.detail || 'Error al convertir el archivo.')
      }
      triggerDownload(await res.blob())
      setStatus({ type: 'success', text: '¡Descarga iniciada! Se usó 1 conversión de tu suscripción.' })
      await checkSubscription()
    } catch (e) {
      setStatus({ type: 'error', text: e.message })
    } finally {
      setBusy(false)
    }
  }

  const triggerDownload = (blob) => {
    const url = URL.createObjectURL(blob)
    const a = Object.assign(document.createElement('a'), { href: url, download: 'estado_cuenta.xlsx' })
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div style={{ display:'flex', alignItems:'center', gap:'var(--ms-space-3)', marginBottom:'var(--ms-space-2)' }}>
        <div className="step-number">2</div>
        <h3 style={{ margin:0, fontSize:'var(--ms-text-xl)', fontWeight:700, color:'var(--ms-text-white)' }}>
          Opciones de Pago
        </h3>
      </div>
      <p className="step-desc">Elige cómo quieres pagar para obtener tu Excel.</p>

      {/* Selector de modo */}
      <div className="payment-mode-selector">
        <button
          className={`btn ${paymentMode === 'onetime' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setPaymentMode('onetime')}
        >
          Pago único — $20 MXN
        </button>
        <button
          className={`btn ${paymentMode === 'subscription' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setPaymentMode('subscription')}
        >
          Suscripción mensual
        </button>
      </div>

      {/* Modo pago único */}
      {paymentMode === 'onetime' && (
        <div className="onetime-payment">
          {conversionsLeft > 0 && (
            <div className="subscription-notice">
              <p>Tienes {conversionsLeft} conversión(es) disponibles en tu suscripción.</p>
              <button className="btn btn-success" disabled={!uploadId || busy} onClick={convertWithSubscription}>
                {busy ? <><span className="ms-spinner"></span> Procesando...</> : 'Usar mi suscripción'}
              </button>
            </div>
          )}

          <div className="row">
            <button className="btn btn-secondary" onClick={onBack}>← Volver</button>

            {!orderId && (
              <button className="btn btn-primary" disabled={!uploadId || busy} onClick={createOrder}>
                {busy ? <><span className="ms-spinner"></span> Creando...</> : 'Crear orden PayPal'}
              </button>
            )}

            {approvalUrl && (
              <a className="paypal-link" href={approvalUrl} target="_blank" rel="noopener noreferrer">
                Pagar con PayPal ↗
              </a>
            )}

            {orderId && (
              <button className="btn btn-success" disabled={!uploadId || busy} onClick={captureAndDownload}>
                {busy ? <><span className="ms-spinner"></span> Procesando...</> : '⬇ Convertir y descargar'}
              </button>
            )}
          </div>

          {orderId && !approvalUrl && (
            <p style={{ color:'var(--ms-text-muted)', fontSize:'var(--ms-text-xs)', marginTop:'var(--ms-space-3)' }}>
              Si ya completaste el pago en PayPal, haz clic en "Convertir y descargar".
            </p>
          )}
        </div>
      )}

      {/* Modo suscripción */}
      {paymentMode === 'subscription' && (
        <div className="subscription-payment">
          {conversionsLeft > 0 ? (
            <div>
              <p style={{ color:'#6ee7b7', fontWeight:600, marginBottom:'var(--ms-space-4)' }}>
                Suscripción activa con {conversionsLeft} conversión(es) disponibles.
              </p>
              <div className="row">
                <button className="btn btn-secondary" onClick={onBack}>← Volver</button>
                <button className="btn btn-success" disabled={!uploadId || busy} onClick={convertWithSubscription}>
                  {busy ? <><span className="ms-spinner"></span> Procesando...</> : '⬇ Convertir con suscripción'}
                </button>
              </div>
            </div>
          ) : (
            <>
              <SubscriptionPlans />
              <div style={{ marginTop:'var(--ms-space-4)' }}>
                <button className="btn btn-secondary" onClick={onBack}>← Volver</button>
              </div>
            </>
          )}
        </div>
      )}

      {status && (
        <div className={`status-msg ${status.type}`} style={{ marginTop:'var(--ms-space-6)' }}>
          {status.text}
        </div>
      )}
    </div>
  )
}
