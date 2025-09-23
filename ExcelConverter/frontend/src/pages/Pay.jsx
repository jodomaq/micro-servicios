import React, { useEffect, useState } from 'react'

export default function Pay({ apiBase, uploadId, onBack }){
  const [orderId, setOrderId] = useState(null)
  const [approvalUrl, setApprovalUrl] = useState(null)
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(()=>{
    const createOrder = async () => {
      try{
        setStatus('Creando orden de PayPal...')
        const res = await fetch(`${apiBase}/converter/paypal/create-order`,{
          method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({})
        })
        if(!res.ok){
          const err = await res.json().catch(()=>({detail:'Error creando orden'}))
          throw new Error(err.detail||'Error creando orden')
        }
  const data = await res.json()
  setOrderId(data.id)
  const link = (data.links||[]).find(l => l.rel === 'approve' || l.rel === 'payer-action')?.href || null
  setApprovalUrl(link)
  setStatus(link ? 'Orden creada. Abre PayPal para pagar.' : 'Orden creada. Si ya pagaste, presiona "Ya pagué"')
      }catch(e){
        setStatus(`Error: ${e.message}`)
      }
    }
    createOrder()
  },[apiBase])

  const pay = async () => {
    if(!orderId){ setStatus('No hay orden'); return }
    // Redirigir a PayPal si viene link approve
    try{
      setBusy(true)
      if(approvalUrl){
        window.open(approvalUrl, '_blank', 'noopener,noreferrer')
        setStatus('Una vez completes el pago, presiona "Ya pagué"')
      } else {
        setStatus('No se pudo obtener el enlace de aprobación, intenta "Ya pagué" si ya completaste.')
      }
    } finally{
      setBusy(false)
    }
  }

  // approvalUrl se obtiene de la respuesta create-order

  const captureAndDownload = async () => {
    if(!orderId){ setStatus('No hay orden'); return }
    setBusy(true)
    setStatus('Verificando pago y convirtiendo...')
    try{
      const res = await fetch(`${apiBase}/converter/paypal/capture-and-convert`,{
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({order_id: orderId, upload_id: uploadId})
      })
      if(res.status === 402){
        const err = await res.json().catch(()=>({detail:'Pago no completado'}))
        throw new Error(err.detail||'Pago no completado')
      }
      if(!res.ok){
        const err = await res.json().catch(()=>({detail:'Error al convertir'}))
        throw new Error(err.detail||'Error al convertir')
      }
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'estado_cuenta.xlsx'
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      setStatus('Descarga iniciada.')
    }catch(e){
      setStatus(`Error: ${e.message}`)
    }finally{
      setBusy(false)
    }
  }

  return (
    <div>
      <h3>2) Paga $20 MXN en PayPal</h3>
      {!uploadId && <p className="error">Primero sube tu archivo.</p>}
      <div className="row">
        <button className="btn" onClick={onBack}>Volver</button>
        <button className="btn" disabled={!orderId||busy} onClick={pay}>Pagar con PayPal</button>
        <button className="btn" disabled={!orderId||!uploadId||busy} onClick={captureAndDownload}>Ya pagué, convertir y descargar</button>
      </div>
      <p className={status.startsWith('Error')? 'error':'success'}>{status}</p>
    </div>
  )
}
