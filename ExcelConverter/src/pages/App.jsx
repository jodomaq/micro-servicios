import React, { useMemo, useState } from 'react'
import Upload from './Upload'
import Pay from './Pay'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App(){
  const [uploadId, setUploadId] = useState(null)
  const [step, setStep] = useState(1)
  const [orderId, setOrderId] = useState(null)

  const goUpload = () => setStep(1)
  const goPay = () => setStep(2)

  const reset = () => {
    setUploadId(null)
    setOrderId(null)
    setStep(1)
  }

  return (
    <div className="container">
      <div className="header">
        <h2>Conversor de Estados de Cuenta a Excel</h2>
        <button className="btn" onClick={reset}>Reiniciar</button>
      </div>
      <div className="card">
        {step === 1 && (
          <Upload apiBase={API_BASE} onUploaded={(id)=>{ setUploadId(id); goPay(); }} />
        )}
        {step === 2 && (
          <Pay apiBase={API_BASE} uploadId={uploadId} onBack={goUpload} />
        )}
      </div>
      <div className="footer">
        <p>1) Sube un PDF (máx 10 páginas). 2) Paga $20 MXN con PayPal. 3) Descarga tu Excel.</p>
      </div>
    </div>
  )
}
