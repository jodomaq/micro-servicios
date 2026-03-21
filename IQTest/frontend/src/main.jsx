import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { PayPalScriptProvider } from '@paypal/react-paypal-js';
import App from './App.jsx';
import '../../../../shared-ui/tokens.css';
import '../../../../shared-ui/components.css';
import './index.css';

const paypalOptions = {
  "client-id": import.meta.env.VITE_PAYPAL_CLIENT_ID || "test",
  currency: "MXN",
  intent: "capture",
};

const rawBase = import.meta.env.VITE_BASE_PATH || '/';
const routerBasename = rawBase === '/' ? undefined : ('/' + rawBase.replace(/^\/+|\/+$/g, ''));

ReactDOM.createRoot(document.getElementById('root')).render(
  <PayPalScriptProvider options={paypalOptions}>
    <BrowserRouter basename={routerBasename}>
      <App />
    </BrowserRouter>
  </PayPalScriptProvider>
);
