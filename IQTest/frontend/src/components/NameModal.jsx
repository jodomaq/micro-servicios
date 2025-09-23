import React, { useState, useEffect } from 'react';
import './Modal.css';

/**
 * Simple reusable modal to capture a user's name
 * Props:
 *  - open: boolean
 *  - defaultValue: string | undefined
 *  - onSave: (name:string)=>void
 *  - onClose: ()=>void
 */
const NameModal = ({ open, defaultValue = '', onSave, onClose }) => {
  const [name, setName] = useState(defaultValue);
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (open) {
      setName(defaultValue || '');
      setTouched(false);
    }
  }, [open, defaultValue]);

  if (!open) return null;

  const handleSave = () => {
    if (!name.trim()) {
      setTouched(true);
      return;
    }
    onSave(name.trim());
  };

  const handleBackdrop = (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdrop}>
      <div className="modal-window" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <h3 id="modal-title">Ingresa tu nombre</h3>
        <p className="modal-desc">Tu nombre aparecerá en el certificado. Puedes dejarlo vacío para usar "Usuario".</p>
        <input
          type="text"
          className="modal-input"
          placeholder="Ej: Juan Pérez"
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoFocus
        />
        {touched && !name.trim() && (
          <div className="modal-error">El nombre no puede estar vacío.</div>
        )}
        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>Cancelar</button>
          <button className="btn btn-primary" onClick={handleSave}>Guardar</button>
        </div>
      </div>
    </div>
  );
};

export default NameModal;
