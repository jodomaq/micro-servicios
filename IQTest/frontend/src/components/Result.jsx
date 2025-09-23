import React, { useState } from 'react';
import { PayPalButtons } from '@paypal/react-paypal-js';
import Certificate from './Certificate.jsx';
import ShareButtons from './ShareButtons.jsx';
import './Result.css';
import { verifyPayment, evaluate, createPayPalOrder, capturePayPalOrder, updateUser } from '../api/api.js';

const Result = ({ userId, onRestart }) => {
  const [paymentComplete, setPaymentComplete] = useState(false);
  const [awaitingName, setAwaitingName] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pendingName, setPendingName] = useState('');
  
  
  const runEvaluation = async (nameForCert) => {
    setLoading(true);
    try {
      const evaluationResponse = await evaluate(userId);
      const mapped = {
        iqScore: evaluationResponse.data?.iq_score ?? evaluationResponse.iq_score,
        strengths: evaluationResponse.data?.strengths ?? evaluationResponse.strengths ?? [],
        weaknesses: evaluationResponse.data?.weaknesses ?? evaluationResponse.weaknesses ?? [],
        detailedReport: evaluationResponse.data?.detailed_report ?? evaluationResponse.detailed_report ?? {},
        certificate_url: evaluationResponse.data?.certificate_url ?? evaluationResponse.certificate_url ?? null,
        name: nameForCert
      };
      setResult(mapped);
    } finally {
      setLoading(false);
    }
  };

  const handlePaypalApprove = async (data, actions) => {
    setLoading(true);
    try {
      // Capturar el pago usando nuestra API
      const orderData = await capturePayPalOrder(data.orderID);
      
      // Verificar si hay errores específicos
      const errorDetail = orderData?.error;
      if (errorDetail === "payment_declined") {
        // Error recuperable, permitir al usuario intentar con otro método de pago
        alert(orderData.message || "El método de pago fue rechazado, por favor intenta con otro método.");
        return actions.restart();
      } else if (errorDetail) {
        // Otro error no recuperable
        throw new Error(orderData.message || "Error al procesar el pago");
      }
      
      // En una app real, aquí verificaríamos el pago con nuestro backend
      const verification = await verifyPayment({
        orderId: orderData.id || data.orderID,
        userId: userId
      });

      // Antes de evaluar pedimos nombre (si no existe ya en localStorage)
      const existingName = localStorage.getItem('iqtest_user_name');
      if (!existingName) {
        setAwaitingName(true);
      } else {
        await runEvaluation(existingName);
      }
      setPaymentComplete(true);
    } catch (error) {
      console.error("Error al procesar el pago:", error);
      
      // Mostrar mensaje amigable para tipos de errores específicos
      if (error.message && error.message.includes("Window closed")) {
        alert("Has cerrado la ventana de PayPal antes de completar el pago. Por favor, intenta nuevamente.");
      } else {
        alert("Ha ocurrido un error al procesar tu pago. Por favor, intenta nuevamente o contacta a soporte.");
      }
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Procesando tu pago y analizando resultados...</p>
      </div>
    );
  }
  
  if (!paymentComplete) {
    return (
      <div className="payment-container">
        <h2>¡Has completado el test!</h2>
        <p className="payment-info">
          Para ver tus resultados detallados, completa el pago de $20 pesos.
        </p>
        
        <div className="benefits-list">
          <h3>Lo que obtendrás:</h3>
          <ul>
            <li>Tu puntuación exacta de coeficiente intelectual</li>
            <li>Análisis de fortalezas y debilidades</li>
            <li>Informe detallado con gráficas comparativas</li>
            <li>Certificado imprimible personalizado</li>
            <li>Opciones para compartir en redes sociales</li>
          </ul>
        </div>
        
        <div className="paypal-container">
          <PayPalButtons
            createOrder={async () => {
              try {
                const orderData = await createPayPalOrder({
                  cart: [
                    {
                      id: "iq-test-results",
                      quantity: 1,
                    },
                  ],
                });
                
                if (orderData.id) {
                  return orderData.id;
                } else {
                  throw new Error("No se pudo crear la orden de PayPal");
                }
              } catch (error) {
                console.error("Error al crear la orden:", error);
                alert("Ha ocurrido un error al iniciar el proceso de pago. Por favor, intenta nuevamente.");
                throw error;
              }
            }}
            onApprove={handlePaypalApprove}
            style={{
              shape: "rect",
              layout: "vertical",
              color: "gold",
              label: "paypal"
            }}
          />
        </div>
      </div>
    );
  }
  
  if (paymentComplete && awaitingName) {
    return (
      <div className="payment-container">
        <h2>Antes de mostrar tu resultado...</h2>
        <p>Ingresa tu nombre tal y como deseas que aparezca en tu certificado.</p>
        <div style={{maxWidth:'400px', margin:'1rem auto', display:'flex', flexDirection:'column', gap:'0.75rem'}}>
          <input
            type="text"
            placeholder="Tu nombre"
            value={pendingName}
            onChange={(e)=>setPendingName(e.target.value)}
            style={{padding:'0.6rem 0.75rem', border:'1px solid #ccc', borderRadius:'6px'}}
          />
          <button
            className="btn btn-primary"
            disabled={!pendingName.trim()}
            onClick={async ()=>{
              const raw = pendingName.trim();
              const formatted = raw.split(/\s+/).map(w=>w.charAt(0).toUpperCase()+w.slice(1).toLowerCase()).join(' ');
              localStorage.setItem('iqtest_user_name', formatted);
              try { await updateUser(userId, { name: formatted }); } catch(e){ console.warn('No se pudo actualizar nombre backend', e); }
              setAwaitingName(false);
              await runEvaluation(formatted);
            }}
          >Continuar</button>
        </div>
      </div>
    );
  }

  return (
    <div className="results-container">
      <div className="score-section">
        <h2>Tu Coeficiente Intelectual</h2>
        <div className="iq-score">{result.iqScore}</div>
        <p className="score-description">
          {result.iqScore > 130 ? "Nivel superior" : 
           result.iqScore > 110 ? "Por encima del promedio" : 
           result.iqScore > 90 ? "Promedio" : "Por debajo del promedio"}
        </p>
      </div>
      
      <div className="analysis-section">
        <div className="strengths">
          <h3>Tus Fortalezas</h3>
          <ul>
            {result.strengths.map((strength, index) => (
              <li key={index}>{strength}</li>
            ))}
          </ul>
        </div>
        
        <div className="weaknesses">
          <h3>Áreas de Mejora</h3>
          <ul>
            {result.weaknesses.map((weakness, index) => (
              <li key={index}>{weakness}</li>
            ))}
          </ul>
        </div>
      </div>
      
      <div className="detailed-report">
        <h3>Informe Detallado</h3>
        <div className="charts">
          {/* Aquí iría un componente de gráficas usando Recharts */}
          <div className="chart-placeholder">
            {Object.entries(result.detailedReport).map(([skill, score]) => (
              <div className="skill-bar" key={skill}>
                <span className="skill-name">{skill.charAt(0).toUpperCase() + skill.slice(1)}</span>
                <div className="skill-progress">
                  <div 
                    className="skill-level" 
                    style={{ width: `${score}%`, backgroundColor: getColorForScore(score) }}
                  ></div>
                </div>
                <span className="skill-percentage">{score}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
  <Certificate result={result} userId={userId} />
      
      <ShareButtons score={result.iqScore} />
      
      <button className="btn btn-secondary retry-btn" onClick={onRestart}>
        Realizar el test nuevamente
      </button>
    </div>
  );
};


// Función auxiliar para obtener colores basados en puntuación
const getColorForScore = (score) => {
  if (score >= 90) return '#34A853'; // Verde para puntajes altos
  if (score >= 70) return '#FBBC05'; // Amarillo para puntajes medios
  return '#EA4335'; // Rojo para puntajes bajos
};

export default Result;