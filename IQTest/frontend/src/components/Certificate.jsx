import React, { useRef, useState, useEffect } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import NameModal from './NameModal.jsx';
import './Modal.css';
import logo from '../assets/logo-micro.png';

const LOCAL_KEY = 'iqtest_user_name';

const capitalizeFullName = (raw) => {
  return raw
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
};

const Certificate = ({ result, userId }) => {
  const certificateRef = useRef(null);
  const [name, setName] = useState('');
  const [showModal, setShowModal] = useState(false); // solo manual ahora
  const [signatureHash, setSignatureHash] = useState('');

  // Load stored name
  useEffect(() => {
    const stored = localStorage.getItem(LOCAL_KEY);
    if (stored) setName(stored);
    // generar hash aleatorio para la "firma" (no persistente)
    const genHash = () => {
      try {
        const bytes = new Uint8Array(16);
        crypto.getRandomValues(bytes);
        return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
      } catch {
        return Math.random().toString(36).slice(2).padEnd(32, 'x');
      }
    };
    setSignatureHash(genHash());
  }, []);

  const handleSaveName = async (newName) => {
    const finalName = newName ? capitalizeFullName(newName) : 'Usuario';
    setName(finalName);
    localStorage.setItem(LOCAL_KEY, finalName);
    setShowModal(false);
    // Actualizar backend de forma silenciosa
    try {
      if (userId) {
        const { updateUser } = await import('../api/api.js');
        await updateUser(userId, { name: finalName });
      }
    } catch (e) {
      console.warn('No se pudo actualizar el nombre en backend:', e);
    }
  };

  const openEdit = () => setShowModal(true);
  
  const downloadAsPDF = () => {
    const input = certificateRef.current;
    
    html2canvas(input, { scale: 2 }).then((canvas) => {
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('landscape', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
      const imgX = (pdfWidth - imgWidth * ratio) / 2;
      const imgY = 0;
      
      pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);
      pdf.save('certificado-iq.pdf');
    });
  };
  
  return (
    <div className="certificate-section">
      <h3>Tu Certificado</h3>
      
      <div className="certificate-container">
        <div className="certificate" ref={certificateRef}>
          <div className="certificate-header">
            <h2>Certificado de Coeficiente Intelectual</h2>
          </div>
          
          <div className="certificate-body">
            <div className="certificate-logo">{<img src={logo} alt="IQ Test" />}</div>
            <p className="certificate-text">
              Este certificado acredita que
            </p>
            <p className="certificate-name" onClick={openEdit} title="Haz clic para editar tu nombre" style={{cursor:'pointer'}}>
              {name || 'Usuario'}
            </p>
            <p className="certificate-text">
              ha completado nuestro Test de Inteligencia y obtenido un
            </p>
            <p className="certificate-score">
              Coeficiente Intelectual de {result.iqScore}
            </p>
            <p className="certificate-date">
              {new Date().toLocaleDateString()}
            </p>
            <div className="certificate-signature">
              <div className="signature-line"></div>
              <p style={{fontFamily:'monospace', fontSize:'0.7rem', letterSpacing:'1px'}}>{signatureHash}</p>
            </div>
          </div>
        </div>
      </div>
      
      <div style={{display:'flex', gap:'1rem', flexWrap:'wrap'}}>
        <button className="btn btn-secondary" onClick={openEdit}>Editar Nombre</button>
        <button className="btn btn-primary download-btn" onClick={downloadAsPDF}>
          Descargar Certificado
        </button>
      </div>
      {result.certificate_url && (
        <div style={{marginTop:'0.75rem', fontSize:'0.8rem'}}>
          URL de certificado (placeholder): <code>{result.certificate_url}</code>
        </div>
      )}

      <NameModal
        open={showModal}
        defaultValue={name}
        onSave={handleSaveName}
        onClose={() => setShowModal(false)}
      />
    </div>
  );
};

export default Certificate;