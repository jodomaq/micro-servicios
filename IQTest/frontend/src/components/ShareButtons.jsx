import React from 'react';

const ShareButtons = ({ score }) => {
  const shareMessage = `¡Acabo de completar un test de IQ y mi puntuación es ${score}! Realiza el tuyo en [URL]`;
  
  const shareToFacebook = () => {
    const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}&quote=${encodeURIComponent(shareMessage)}`;
    window.open(url, '_blank');
  };
  
  const shareToTwitter = () => {
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareMessage)}&url=${encodeURIComponent(window.location.href)}`;
    window.open(url, '_blank');
  };
  
  const shareToWhatsApp = () => {
    const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareMessage + ' ' + window.location.href)}`;
    window.open(url, '_blank');
  };
  
  const shareToInstagram = () => {
    // Instagram no tiene una API de compartir directa como otros,
    // normalmente se comparte a través de historias con una integración más profunda
    alert('Para compartir en Instagram, toma una captura de pantalla de tu certificado y súbela a tus historias.');
  };
  
  return (
    <div className="share-section">
      <h3>Comparte tu Resultado</h3>
      
      <div className="share-buttons">
        <button className="share-btn facebook" onClick={shareToFacebook}>
          <i className="facebook-icon">f</i>
          Facebook
        </button>
        
        <button className="share-btn twitter" onClick={shareToTwitter}>
          <i className="twitter-icon">𝕏</i>
          Twitter/X
        </button>
        
        <button className="share-btn instagram" onClick={shareToInstagram}>
          <i className="instagram-icon">📷</i>
          Instagram
        </button>
        
        <button className="share-btn whatsapp" onClick={shareToWhatsApp}>
          <i className="whatsapp-icon">W</i>
          WhatsApp
        </button>
      </div>
    </div>
  );
};

export default ShareButtons;