import axios from 'axios'

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api',
})

// Tenant header
api.interceptors.request.use((config) => {
  const tenantId = import.meta.env.VITE_TENANT_ID || '1'
  config.headers['X-Tenant-ID'] = tenantId
  return config
})

export default api
