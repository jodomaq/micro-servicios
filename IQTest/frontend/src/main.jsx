import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { PayPalScriptProvider } from '@paypal/react-paypal-js';
import App from './App.jsx';
import './index.css';

// Configuración de PayPal
const paypalOptions = {
  "client-id": "AYJPAOcofc2w51eYx9ZpYhNsVzhjcrOGyMZOa2VydOl9nvVI6BcoaEM7dYVqyHHYaFUkrjsV2eN_A8th", // Usa "test" para el entorno de pruebas
  currency: "MXN",
  intent: "capture"
};

// Determinar basename para BrowserRouter a partir de VITE_BASE_PATH
const rawBase = import.meta.env.VITE_BASE_PATH || '/';
// Normalizamos: '/quiz/' -> '/quiz'; '/' permanece '/'
const routerBasename = rawBase === '/' ? '/' : ('/' + rawBase.replace(/^\/+|\/+$/g, ''));

ReactDOM.createRoot(document.getElementById('root')).render(
  <PayPalScriptProvider options={paypalOptions}>
    <BrowserRouter basename={routerBasename === '/' ? undefined : routerBasename}>
      <App />
    </BrowserRouter>
  </PayPalScriptProvider>
);