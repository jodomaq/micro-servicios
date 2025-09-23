import React, { useState } from 'react'

export default function Upload({ apiBase, onUploaded }){
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  const onFile = (e) => {
    const f = e.target.files?.[0]
    if(!f) return
    if(!f.name.toLowerCase().endsWith('.pdf')){
      setStatus('Solo se acepta PDF')
      return
    }
    if(f.size > 15*1024*1024){ // 15MB guardrail
      setStatus('Archivo demasiado grande (máx ~15MB).')
      return
    }
    setFile(f)
    setStatus('')
  }

  const upload = async () => {
    if(!file) return
    setBusy(true)
    setStatus('Subiendo...')
    const form = new FormData()
    form.append('file', file)
    try{
      const res = await fetch(`${apiBase}/converter/upload`, { method:'POST', body: form })
      if(!res.ok){
        const err = await res.json().catch(()=>({detail:'Error al subir'}))
        throw new Error(err.detail || 'Error al subir')
      }
      const data = await res.json()
      setStatus('Listo. Continúa con el pago.')
      onUploaded?.(data.upload_id)
    }catch(e){
      setStatus(`Error: ${e.message}`)
    }finally{
      setBusy(false)
    }
  }

  return (
    <div>
      <h3>1) Sube tu PDF</h3>
      <p>Estados de cuenta con máximo 10 páginas.</p>
      <div className="row">
        <input className="input" type="file" accept="application/pdf" onChange={onFile} />
        <button className="btn" disabled={!file||busy} onClick={upload}>Subir</button>
      </div>
      <p className={status.startsWith('Error')? 'error':'success'}>{status}</p>
    </div>
  )
}
