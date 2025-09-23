import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  return (
    <div className="home-container">
      <header className="hero">
        <div className="container">
          <h1>Descubre tu Coeficiente Intelectual</h1>
          <p className="subtitle">Test de IQ profesional con análisis detallado de tus habilidades cognitivas</p>
          <Link to="/quiz" className="btn btn-primary">Iniciar Test</Link>
        </div>
      </header>

      <section className="benefits container">
        <h2>¿Por qué realizar nuestro Test de IQ?</h2>
        
        <div className="benefits-grid">
          <div className="benefit-card">
            <div className="icon">🧠</div>
            <h3>Conoce tu potencial</h3>
            <p>Descubre tu verdadero coeficiente intelectual con un test validado científicamente.</p>
          </div>
          
          <div className="benefit-card">
            <div className="icon">💪</div>
            <h3>Identifica tus fortalezas</h3>
            <p>Reconoce las áreas donde destacas para potenciar tu desarrollo personal y profesional.</p>
          </div>
          
          <div className="benefit-card">
            <div className="icon">🔍</div>
            <h3>Mejora tus debilidades</h3>
            <p>Identifica áreas de mejora y recibe recomendaciones personalizadas.</p>
          </div>
          
          <div className="benefit-card">
            <div className="icon">📊</div>
            <h3>Análisis detallado</h3>
            <p>Recibe un informe completo con gráficas y comparativas para entender tus resultados.</p>
          </div>
        </div>
        
        <div className="cta-section">
          <h2>¿Listo para descubrir tu IQ?</h2>
          <p>Solo necesitas 15 minutos para completar el test y obtener resultados profesionales</p>
          <Link to="/quiz" className="btn btn-primary">Comenzar Ahora</Link>
        </div>
      </section>

      <section className="how-it-works container">
        <h2>¿Cómo funciona?</h2>
        
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h3>Responde 20 preguntas</h3>
            <p>Preguntas diseñadas para evaluar diferentes aspectos de tu inteligencia.</p>
          </div>
          
          <div className="step">
            <div className="step-number">2</div>
            <h3>Procesamiento avanzado</h3>
            <p>Nuestro sistema analiza tus respuestas utilizando tecnología de IA avanzada.</p>
          </div>
          
          <div className="step">
            <div className="step-number">3</div>
            <h3>Recibe tu informe completo</h3>
            <p>Por solo 20 pesos, obtén un análisis detallado y tu certificado imprimible.</p>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <p>&copy; {new Date().getFullYear()} Test de IQ - Todos los derechos reservados</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;