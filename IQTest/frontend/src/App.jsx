import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './pages/Home.jsx';
import Quiz from './pages/Quiz.jsx';
import './App.css';

function App() {
  const location = useLocation();
  const onQuiz = location.pathname === '/quiz';

  return (
    <div className="app-container">
      <nav className="ms-nav">
        <div className="ms-nav__brand">
          <a href="/" className="ms-nav__logo-link" title="Micro-Servicios">
            <span className="ms-nav__logo-icon">⚡</span>
            <span className="ms-nav__logo-text">Micro<strong>Servicios</strong></span>
          </a>
          <span className="ms-nav__separator">/</span>
          <span className="ms-nav__app-name">Test de IQ</span>
        </div>
        <div className="ms-nav__links">
          <Link to="/" className={`ms-nav__link${!onQuiz ? ' ms-nav__link--active' : ''}`}>Inicio</Link>
          <Link to="/quiz" className={`ms-nav__link${onQuiz ? ' ms-nav__link--active' : ''}`}>Realizar Test</Link>
        </div>
      </nav>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/quiz" element={<Quiz />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} Micro-Servicios — Test de IQ. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}

export default App;