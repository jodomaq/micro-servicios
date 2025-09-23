import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home.jsx';
import Quiz from './pages/Quiz.jsx';
import './App.css';
import logo from './assets/logo-micro.png';

function App() {
  return (

    <div className="app-container">
      <header className="app-header">
        <div className="logo">
          <img height={50} src={logo} alt="IQ Test" />
        </div>
        <nav className="main-nav">
          <Link to="/" className="nav-link">Inicio</Link>
          <Link to="/quiz" className="nav-link">Realizar Test</Link>
        </nav>
      </header>
      
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/quiz" element={<Quiz />} />
        </Routes>
      </main>
      
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} IQ Test. Todos los derechos reservados.</p>
      </footer>
    </div>

  );
}

export default App;