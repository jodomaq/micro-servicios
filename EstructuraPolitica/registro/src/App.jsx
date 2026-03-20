/**
 * Registro - Landing page pública para registro de nuevos tenants
 * 
 * Secciones:
 * 1. Hero con CTA
 * 2. Features grid
 * 3. Planes de suscripción (desde API /public/plans)
 * 4. Formulario de registro (llama a /public/register-tenant)
 * 5. Verificación de subdominio en tiempo real (/public/check-subdomain/)
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import api from './services/api'

const FEATURES = [
  { icon: '📊', title: 'Dashboard Inteligente', desc: 'Visualiza estadísticas en tiempo real con gráficas y mapas interactivos.' },
  { icon: '👥', title: 'Gestión de Comités', desc: 'Administra comités seccionales con miembros, documentos y estructura jerárquica.' },
  { icon: '📋', title: 'Control de Asistencia', desc: 'Registro de asistencia a eventos con geolocalización y exportación a Excel.' },
  { icon: '🗳️', title: 'Encuestas', desc: 'Crea y distribuye encuestas con resultados en tiempo real.' },
  { icon: '🔒', title: 'Multi-tenant Seguro', desc: 'Cada organización tiene su espacio aislado y seguro con subdominio propio.' },
  { icon: '📱', title: 'Responsivo', desc: 'Funciona en cualquier dispositivo: escritorio, tablet y móvil.' },
]

export default function App() {
  const [view, setView] = useState('landing') // landing | register | success
  const [plans, setPlans] = useState([])
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [registrationResult, setRegistrationResult] = useState(null)

  // Load plans
  useEffect(() => {
    api.get('/public/plans').then(r => setPlans(r.data)).catch(() => {
      // fallback plans
      setPlans([
        { id: 1, name: 'Trial', price_monthly: 0, max_users: 5, max_committees: 10, features: 'Prueba gratuita por 7 días' },
        { id: 2, name: 'Básico', price_monthly: 499, max_users: 20, max_committees: 50, features: 'Ideal para municipios pequeños' },
        { id: 3, name: 'Profesional', price_monthly: 999, max_users: 100, max_committees: 500, features: 'Para distritos y regiones' },
      ])
    })
  }, [])

  if (view === 'success') {
    return <SuccessPage data={registrationResult} onBack={() => setView('landing')} />
  }

  if (view === 'register') {
    return (
      <>
        <Nav onHome={() => setView('landing')} />
        <RegisterForm
          plans={plans}
          selectedPlan={selectedPlan}
          onSuccess={(data) => { setRegistrationResult(data); setView('success') }}
          onBack={() => setView('landing')}
        />
        <Footer />
      </>
    )
  }

  return (
    <>
      <Nav onHome={() => setView('landing')} />

      {/* Hero */}
      <section className="hero">
        <h1>Gestión Electoral Moderna</h1>
        <p>
          Plataforma integral para la administración de comités, asistencia a eventos,
          encuestas y estructura territorial. Tu organización política con tecnología de vanguardia.
        </p>
        <button className="hero-btn" onClick={() => setView('register')}>
          Comienza Gratis →
        </button>
      </section>

      {/* Features */}
      <section className="features">
        {FEATURES.map((f, i) => (
          <div className="feature-card" key={i}>
            <div className="feature-icon">{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Plans */}
      <section className="plans-section" id="planes">
        <h2>Planes</h2>
        <div className="plans-grid">
          {plans.map((plan, i) => (
            <div
              key={plan.id}
              className={`plan-card${i === 1 ? ' recommended' : ''}`}
            >
              <div className="plan-name">{plan.name}</div>
              <div className="plan-price">
                {plan.price_monthly === 0 ? 'Gratis' : `$${plan.price_monthly}`}
                {plan.price_monthly > 0 && <span>/mes</span>}
              </div>
              <ul className="plan-features">
                <li>{plan.max_users} usuarios</li>
                <li>{plan.max_committees} comités</li>
                {plan.features && <li>{plan.features}</li>}
              </ul>
              <button
                className="plan-btn"
                onClick={() => { setSelectedPlan(plan); setView('register') }}
              >
                {plan.price_monthly === 0 ? 'Probar Gratis' : 'Seleccionar'}
              </button>
            </div>
          ))}
        </div>
      </section>

      <Footer />
    </>
  )
}

function Nav({ onHome }) {
  return (
    <nav className="nav">
      <a href="#" className="nav-brand" onClick={(e) => { e.preventDefault(); onHome() }}>
        🏛️ EstructuraPolítica
      </a>
      <div>
        <a href="#planes" onClick={(e) => { e.preventDefault(); document.getElementById('planes')?.scrollIntoView({ behavior: 'smooth' }) }}>
          Planes
        </a>
      </div>
    </nav>
  )
}

function Footer() {
  return (
    <footer className="site-footer">
      © {new Date().getFullYear()} EstructuraPolítica — Plataforma de Gestión Electoral Multi-tenant
    </footer>
  )
}

function SuccessPage({ data, onBack }) {
  return (
    <div className="success-page">
      <div className="big-check">✅</div>
      <h1>¡Registro Exitoso!</h1>
      <p>Tu organización ha sido creada y está lista para usar.</p>

      <div className="info-box">
        <p><strong>Organización:</strong> {data?.tenant_name}</p>
        <p><strong>Subdominio:</strong> {data?.subdomain}.estructura.politica.mx</p>
        <p><strong>Email admin:</strong> {data?.admin_email}</p>
        <p><strong>Plan:</strong> Trial (7 días gratis)</p>
        <p style={{ marginTop: 12, fontSize: '0.9rem', color: '#666' }}>
          Inicia sesión en tu panel con el email registrado para comenzar a configurar tu organización.
        </p>
      </div>

      <button
        className="btn-submit"
        style={{ marginTop: 24 }}
        onClick={onBack}
      >
        Volver al Inicio
      </button>
    </div>
  )
}

function RegisterForm({ plans, selectedPlan, onSuccess, onBack }) {
  const [form, setForm] = useState({
    tenant_name: '',
    subdomain: '',
    admin_name: '',
    admin_email: '',
    admin_password: '',
    plan_id: selectedPlan?.id || '',
  })
  const [subdomainStatus, setSubdomainStatus] = useState(null) // null | 'checking' | 'available' | 'taken'
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const checkTimeout = useRef(null)

  // Auto-generate subdomain from tenant name
  const generateSubdomain = useCallback((name) => {
    return name
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 30)
  }, [])

  function handleChange(field) {
    return (e) => {
      const value = e.target.value
      setForm(prev => {
        const updated = { ...prev, [field]: value }
        if (field === 'tenant_name') {
          updated.subdomain = generateSubdomain(value)
        }
        return updated
      })
      if (field === 'tenant_name') {
        const sub = generateSubdomain(value)
        checkSubdomain(sub)
      }
      if (field === 'subdomain') {
        checkSubdomain(value)
      }
    }
  }

  function checkSubdomain(subdomain) {
    clearTimeout(checkTimeout.current)
    if (!subdomain || subdomain.length < 3) {
      setSubdomainStatus(null)
      return
    }
    setSubdomainStatus('checking')
    checkTimeout.current = setTimeout(async () => {
      try {
        const { data } = await api.get(`/public/check-subdomain/${subdomain}`)
        setSubdomainStatus(data.available ? 'available' : 'taken')
      } catch {
        setSubdomainStatus(null)
      }
    }, 500)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (subdomainStatus === 'taken') return

    setSubmitting(true)
    setError(null)
    try {
      const payload = {
        tenant_name: form.tenant_name,
        subdomain: form.subdomain,
        admin_name: form.admin_name,
        admin_email: form.admin_email,
        admin_password: form.admin_password || 'temp123',
        plan_id: form.plan_id || null,
      }
      const { data } = await api.post('/public/register-tenant', payload)
      onSuccess({
        tenant_name: form.tenant_name,
        subdomain: form.subdomain,
        admin_email: form.admin_email,
        ...data,
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al registrar. Inténtalo de nuevo.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="register-section">
      <h2>Registra tu Organización</h2>
      <p className="subtitle">
        <span className="trial-badge">7 días de prueba gratis</span>
      </p>

      <div className="form-card">
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Nombre de la Organización *</label>
            <input
              type="text"
              value={form.tenant_name}
              onChange={handleChange('tenant_name')}
              placeholder="Ej: Comité Estatal Sonora"
              required
            />
          </div>

          <div className="form-group">
            <label>Subdominio *</label>
            <input
              type="text"
              value={form.subdomain}
              onChange={handleChange('subdomain')}
              placeholder="mi-organizacion"
              required
              minLength={3}
              pattern="[a-z0-9\-]+"
            />
            <div className="subdomain-preview">
              <span className="domain">{form.subdomain || '___'}</span>.estructura.politica.mx
              {subdomainStatus === 'checking' && (
                <span className="subdomain-check" style={{ color: '#999' }}>verificando...</span>
              )}
              {subdomainStatus === 'available' && (
                <span className="subdomain-check available">✓ Disponible</span>
              )}
              {subdomainStatus === 'taken' && (
                <span className="subdomain-check taken">✗ No disponible</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label>Tu Nombre *</label>
            <input
              type="text"
              value={form.admin_name}
              onChange={handleChange('admin_name')}
              placeholder="Nombre del administrador"
              required
            />
          </div>

          <div className="form-group">
            <label>Correo Electrónico *</label>
            <input
              type="email"
              value={form.admin_email}
              onChange={handleChange('admin_email')}
              placeholder="admin@tudominio.com"
              required
            />
          </div>

          <div className="form-group">
            <label>Contraseña *</label>
            <input
              type="password"
              value={form.admin_password}
              onChange={handleChange('admin_password')}
              placeholder="Mínimo 6 caracteres"
              required
              minLength={6}
            />
          </div>

          {plans.length > 0 && (
            <div className="form-group">
              <label>Plan</label>
              <select value={form.plan_id} onChange={handleChange('plan_id')}>
                <option value="">Trial (Gratis - 7 días)</option>
                {plans.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} {p.price_monthly > 0 ? `- $${p.price_monthly}/mes` : ''}
                  </option>
                ))}
              </select>
              <div className="help">Todos los planes comienzan con 7 días de prueba gratuita.</div>
            </div>
          )}

          <button
            type="submit"
            className="btn-submit"
            disabled={submitting || subdomainStatus === 'taken'}
          >
            {submitting ? (
              <><span className="spinner-inline"></span>Registrando...</>
            ) : (
              'Crear mi Organización'
            )}
          </button>
        </form>
      </div>

      <p style={{ textAlign: 'center', marginTop: 16 }}>
        <a href="#" onClick={(e) => { e.preventDefault(); onBack() }} style={{ color: '#999' }}>
          ← Volver al inicio
        </a>
      </p>
    </section>
  )
}
