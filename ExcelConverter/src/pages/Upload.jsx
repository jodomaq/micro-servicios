import React, { useState, useRef } from 'react'

export default function Upload({ apiBase, onUploaded }) {
  const [file, setFile]     = useState(null)
  const [status, setStatus] = useState(null)   // { type: 'error'|'success'|'info', text: string }
  const [busy, setBusy]     = useState(false)
  const inputRef = useRef(null)

  const validateAndSet = (f) => {
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      setStatus({ type: 'error', text: 'Solo se aceptan archivos PDF.' })
      return
    }
    if (f.size > 15 * 1024 * 1024) {
      setStatus({ type: 'error', text: 'El archivo es demasiado grande (máx. 15 MB).' })
      return
    }
    setFile(f)
    setStatus({ type: 'info', text: `Archivo seleccionado: ${f.name} (${(f.size / 1024).toFixed(0)} KB)` })
  }

  const onFileChange = (e) => validateAndSet(e.target.files?.[0])

  const onDrop = (e) => {
    e.preventDefault()
    validateAndSet(e.dataTransfer.files?.[0])
  }

  const upload = async () => {
    if (!file) return
    setBusy(true)
    setStatus({ type: 'info', text: 'Subiendo archivo...' })
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${apiBase}/converter/upload`, { method: 'POST', body: form })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error al subir el archivo.' }))
        throw new Error(err.detail || 'Error al subir el archivo.')
      }
      const data = await res.json()
      setStatus({ type: 'success', text: '¡Archivo subido correctamente! Continúa con el pago.' })
      onUploaded?.(data.upload_id)
    } catch (e) {
      setStatus({ type: 'error', text: e.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div style={{ display:'flex', alignItems:'center', gap:'var(--ms-space-3)', marginBottom:'var(--ms-space-2)' }}>
        <div className="step-number">1</div>
        <h3 style={{ margin:0, fontSize:'var(--ms-text-xl)', fontWeight:700, color:'var(--ms-text-white)' }}>
          Sube tu PDF
        </h3>
      </div>
      <p className="step-desc">Estados de cuenta bancarios, máximo 10 páginas.</p>

      {/* Drop zone */}
      <div
        style={{
          border: `2px dashed ${file ? 'rgba(99,102,241,0.6)' : 'rgba(99,102,241,0.25)'}`,
          borderRadius: 'var(--ms-radius-xl)',
          padding: 'var(--ms-space-12)',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'border-color var(--ms-ease-fast), background var(--ms-ease-fast)',
          background: file ? 'rgba(99,102,241,0.05)' : 'transparent'
        }}
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        onDragEnter={(e) => e.currentTarget.style.borderColor = 'var(--ms-primary)'}
        onDragLeave={(e) => e.currentTarget.style.borderColor = file ? 'rgba(99,102,241,0.6)' : 'rgba(99,102,241,0.25)'}
      >
        <div style={{ fontSize:'3rem', marginBottom:'var(--ms-space-3)' }}>📄</div>
        {file ? (
          <p style={{ margin:0, fontWeight:600, color:'var(--ms-text-white)' }}>{file.name}</p>
        ) : (
          <>
            <p style={{ margin:'0 0 var(--ms-space-2) 0', fontWeight:600, color:'var(--ms-text-white)' }}>
              Arrastra tu PDF aquí
            </p>
            <p style={{ margin:0, color:'var(--ms-text-muted)', fontSize:'var(--ms-text-sm)' }}>
              o haz clic para seleccionar
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          style={{ display:'none' }}
          onChange={onFileChange}
        />
      </div>

      <div className="row">
        {file && (
          <button
            style={{ color:'var(--ms-text-muted)', background:'transparent', border:'none', cursor:'pointer', fontSize:'var(--ms-text-sm)' }}
            onClick={() => { setFile(null); setStatus(null); if(inputRef.current) inputRef.current.value='' }}
          >
            Cambiar archivo
          </button>
        )}
        <button
          className="btn btn-primary"
          disabled={!file || busy}
          onClick={upload}
          style={{ marginLeft:'auto' }}
        >
          {busy
            ? <><span className="ms-spinner"></span> Subiendo...</>
            : 'Subir y continuar →'}
        </button>
      </div>

      {status && (
        <div className={`status-msg ${status.type}`} style={{ marginTop:'var(--ms-space-4)' }}>
          {status.text}
        </div>
      )}
    </div>
  )
}
