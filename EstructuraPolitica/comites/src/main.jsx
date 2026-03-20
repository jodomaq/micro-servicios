import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { MsalProvider } from '@azure/msal-react'
import { PublicClientApplication } from '@azure/msal-browser'

// MSAL configuration for Microsoft OAuth
const msalConfig = {
    auth: {
        clientId: import.meta.env.VITE_MICROSOFT_CLIENT_ID || '',
        authority: 'https://login.microsoftonline.com/common',
        redirectUri: window.location.origin,
    },
    cache: {
        cacheLocation: 'sessionStorage',
        storeAuthStateInCookie: false,
    },
}

const msalInstance = new PublicClientApplication(msalConfig)

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <BrowserRouter>
            <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ''}>
                <MsalProvider instance={msalInstance}>
                    <App />
                </MsalProvider>
            </GoogleOAuthProvider>
        </BrowserRouter>
    </React.StrictMode>,
)
