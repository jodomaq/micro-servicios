import React, { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import SubscriptionPlans from '../components/SubscriptionPlans'

export default function Pay({ apiBase, uploadId, onBack }){
  const { user, getAuthHeader } = useAuth()
  const [orderId, setOrderId] = useState(null)
  const [approvalUrl, setApprovalUrl] = useState(null)
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)
  const [paymentMode, setPaymentMode] = useState('onetime') // 'onetime' or 'subscription'
  const [canConvertWithSubscription, setCanConvertWithSubscription] = useState(false)

  useEffect(() => {
    // Check if user has active subscription with available conversions
    if (user) {
      checkSubscriptionStatus()
    }
  }, [user])

  const checkSubscriptionStatus = async () => {
    try {
      const res = await fetch(`${apiBase}/subscriptions/dashboard`, {
        headers: getAuthHeader()
      })
      if (res.ok) {
        const data = await res.json()
        const hasConversions = data.conversions_remaining > 0
        setCanConvertWithSubscription(hasConversions)
        if (hasConversions) {
          setStatus(`Tienes ${data.conversions_remaining} conversiones disponibles en tu suscripción`)
        }
      }
    } catch (e) {
      console.error('Error checking subscription:', e)
    }
  }

  const createOneTimeOrder = async () => {
    try {
      setStatus('Creando orden de PayPal...')
      setBusy(true)
      const res = await fetch(`${apiBase}/converter/paypal/create-order`,{
        method:'POST', 
        headers:{'Content-Type':'application/json'}, 
        body: JSON.stringify({})
      })
      if(!res.ok){
        const err = await res.json().catch(()=>({detail:'Error creando orden'}))
        throw new Error(err.detail||'Error creando orden')
      }
      const data = await res.json()
      setOrderId(data.id)
      const link = (data.links||[]).find(l => l.rel === 'approve' || l.rel === 'payer-action')?.href || null
      setApprovalUrl(link)
      setStatus(link ? 'Orden creada. Abre PayPal para pagar.' : 'Orden creada. Si ya pagaste, presiona "Convertir y descargar"')
    } catch(e) {
      setStatus(`Error: ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  const openPayPal = () => {
    if (approvalUrl) {
      window.open(approvalUrl, '_blank')
    }
  }

  const convertWithSubscription = async () => {
    if (!user) {
      setStatus('Debes iniciar sesión para usar tu suscripción')
      return
    }

    if (!uploadId) {
      setStatus('Primero sube tu archivo.')
      return
    }

    setBusy(true)
    setStatus('Convirtiendo archivo con tu suscripción...')
    
    try {
      const res = await fetch(`${apiBase}/converter/convert`, {
        method:'POST',
        headers:{
          'Content-Type':'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({ upload_id: uploadId })
      })

      if(!res.ok){
        const err = await res.json().catch(()=>({detail:'Error al convertir'}))
        throw new Error(err.detail||'Error al convertir')
      }
      
      const blob = await res.blob()
      downloadFile(blob)
      setStatus('Descarga iniciada. Conversión restada de tu suscripción.')
      
      // Refresh subscription status
      await checkSubscriptionStatus()
    } catch(e) {
      setStatus(`Error: ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  const captureAndDownload = async () => {
    if (!orderId) {
      setStatus('Primero crea una orden de pago.')
      return
    }
    
    if (!uploadId) {
      setStatus('Primero sube tu archivo.')
      return
    }

    setBusy(true)
    setStatus('Capturando pago y convirtiendo archivo...')
    
    try {
      const res = await fetch(`${apiBase}/converter/paypal/capture-and-convert`,{
        method:'POST', 
        headers:{
          'Content-Type':'application/json',
          ...getAuthHeader()
        }, 
        body: JSON.stringify({order_id: orderId, upload_id: uploadId})
      })

      if(!res.ok){
        const err = await res.json().catch(()=>({detail:'Error al convertir'}))
        throw new Error(err.detail||'Error al convertir')
      }
      
      const blob = await res.blob()
      downloadFile(blob)
      setStatus('Descarga iniciada.')
    } catch(e) {
      setStatus(`Error: ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  const downloadFile = (blob) => {
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'estado_cuenta.xlsx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div>
      <h3>2) Opciones de Pago</h3>
      
      {!uploadId && <p className="error">Primero sube tu archivo.</p>}

      <div className="payment-mode-selector">
        <button 
          className={`btn ${paymentMode === 'onetime' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setPaymentMode('onetime')}
        >
          Pago Único ($20 MXN)
        </button>
        <button 
          className={`btn ${paymentMode === 'subscription' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setPaymentMode('subscription')}
        >
          Suscripción Mensual
        </button>
      </div>

      {paymentMode === 'onetime' ? (
        <div className="onetime-payment">
          <p>Paga $20 MXN por esta conversión única</p>
          
          {canConvertWithSubscription && (
            <div className="subscription-notice">
              <p>💡 Tienes conversiones disponibles en tu suscripción. Úsalas para no pagar extra.</p>
              <button className="btn btn-success" disabled={!uploadId||busy} onClick={convertWithSubscription}>
                Usar Suscripción
              </button>
            </div>
          )}

          <div className="row">
            <button className="btn" onClick={onBack}>Volver</button>
            {!orderId && (
              <button className="btn btn-primary" disabled={!uploadId||busy} onClick={createOneTimeOrder}>
                Crear Orden PayPal
              </button>
            )}
            {approvalUrl && (
              <button className="btn btn-primary" onClick={openPayPal}>
                Abrir PayPal para Pagar
              </button>
            )}
            {orderId && (
              <button className="btn btn-success" disabled={!uploadId||busy} onClick={captureAndDownload}>
                Convertir y Descargar
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="subscription-payment">
          {canConvertWithSubscription ? (
            <div>
              <p className="success">¡Tienes una suscripción activa!</p>
              <button className="btn btn-success" disabled={!uploadId||busy} onClick={convertWithSubscription}>
                Convertir con Suscripción
              </button>
            </div>
          ) : (
            <SubscriptionPlans />
          )}
          <button className="btn btn-secondary" onClick={onBack}>Volver</button>
        </div>
      )}

      <p className={status.startsWith('Error')? 'error':'success'}>{status}</p>
    </div>
  )
}
