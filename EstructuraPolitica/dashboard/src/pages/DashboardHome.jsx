/**
 * Dashboard Home - Resumen general con gráficos
 */
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../services/api'

const COLORS = ['#1976d2', '#2e7d32', '#ff6f00', '#c62828', '#7b1fa2', '#0097a7', '#afb42b', '#5d4037']

export default function DashboardHome() {
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/dashboard/stats').then(r => r.data),
  })
  const { data: byType } = useQuery({
    queryKey: ['committees-by-type'],
    queryFn: () => api.get('/dashboard/committees/by-type').then(r => r.data),
  })
  const { data: growth } = useQuery({
    queryKey: ['committees-growth'],
    queryFn: () => api.get('/dashboard/committees/growth').then(r => r.data),
  })
  const { data: surveysSummary } = useQuery({
    queryKey: ['surveys-summary'],
    queryFn: () => api.get('/dashboard/surveys/summary').then(r => r.data),
  })

  if (loadingStats) return <div className="loading"><div className="spinner"></div></div>

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Resumen General</h1>

      {/* Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats?.total_committees ?? 0}</div>
          <div className="stat-label">Comités</div>
        </div>
        <div className="stat-card success">
          <div className="stat-value">{stats?.total_members ?? 0}</div>
          <div className="stat-label">Miembros</div>
        </div>
        <div className="stat-card warning">
          <div className="stat-value">{stats?.total_users ?? 0}</div>
          <div className="stat-label">Usuarios</div>
        </div>
        <div className="stat-card error">
          <div className="stat-value">{stats?.total_events ?? 0}</div>
          <div className="stat-label">Eventos</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-grid">
        {/* Committees by Type - Pie */}
        <div className="card chart-card">
          <div className="card-header"><h3>Comités por Tipo</h3></div>
          {byType && byType.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={byType} dataKey="count" nameKey="type_name" cx="50%" cy="50%" outerRadius={100} label={({ name, value }) => `${name}: ${value}`}>
                  {byType.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p style={{ textAlign: 'center', color: '#999', padding: 40 }}>Sin datos</p>}
        </div>

        {/* Growth - Line */}
        <div className="card chart-card">
          <div className="card-header"><h3>Crecimiento de Comités</h3></div>
          {growth && growth.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={growth}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#1976d2" strokeWidth={2} dot={{ fill: '#1976d2' }} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p style={{ textAlign: 'center', color: '#999', padding: 40 }}>Sin datos</p>}
        </div>
      </div>

      {/* Surveys Summary */}
      {surveysSummary && surveysSummary.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><h3>Encuestas Activas</h3></div>
          <table className="data-table">
            <thead>
              <tr><th>Título</th><th>Respuestas</th><th>Estado</th></tr>
            </thead>
            <tbody>
              {surveysSummary.map((s, i) => (
                <tr key={i}>
                  <td>{s.title}</td>
                  <td>{s.response_count ?? 0}</td>
                  <td><span className={`chip ${s.is_active ? 'success' : 'warning'}`}>{s.is_active ? 'Activa' : 'Inactiva'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
