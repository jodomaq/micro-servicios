import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './pages/App'
import { AuthProvider } from './context/AuthContext'
import '../../shared-ui/tokens.css'
import '../../shared-ui/components.css'
import './style.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
)
