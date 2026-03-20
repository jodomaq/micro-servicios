/**
 * Committees Statistics Page
 */
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import api from '../services/api'

const COLORS = ['#1976d2', '#2e7d32', '#ff6f00', '#c62828', '#7b1fa2', '#0097a7', '#afb42b', '#5d4037']

export default function CommitteesStats() {
  const { data: byType, isLoading: l1 } = useQuery({
    queryKey: ['committees-by-type'],
    queryFn: () => api.get('/dashboard/committees/by-type').then(r => r.data),
  })
  const { data: byUnit } = useQuery({
    queryKey: ['committees-by-unit'],
    queryFn: () => api.get('/dashboard/committees/by-unit').then(r => r.data),
  })
  const { data: byCoordinator } = useQuery({
    queryKey: ['committees-by-coordinator'],
    queryFn: () => api.get('/dashboard/committees/by-coordinator').then(r => r.data),
  })
  const { data: byReferrer } = useQuery({
    queryKey: ['members-by-referrer'],
    queryFn: () => api.get('/dashboard/members/by-referrer').then(r => r.data),
  })

  if (l1) return <div className="loading"><div className="spinner"></div></div>

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Estadísticas de Comités</h1>

      <div className="charts-grid">
        {/* By Type */}
        <div className="card chart-card">
          <div className="card-header"><h3>Por Tipo</h3></div>
          {byType?.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={byType} dataKey="count" nameKey="type_name" cx="50%" cy="50%" outerRadius={100} label>
                  {byType.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <p style={{ textAlign: 'center', color: '#999', padding: 40 }}>Sin datos</p>}
        </div>

        {/* By Unit */}
        <div className="card chart-card">
          <div className="card-header"><h3>Por Unidad Administrativa</h3></div>
          {byUnit?.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={byUnit.slice(0, 10)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="unit_name" width={120} />
                <Tooltip />
                <Bar dataKey="count" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
          ) : <p style={{ textAlign: 'center', color: '#999', padding: 40 }}>Sin datos</p>}
        </div>
      </div>

      {/* By Coordinator Table */}
      {byCoordinator?.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><h3>Top Coordinadores</h3></div>
          <table className="data-table">
            <thead><tr><th>Coordinador</th><th>Comités</th></tr></thead>
            <tbody>
              {byCoordinator.slice(0, 15).map((c, i) => (
                <tr key={i}><td>{c.coordinator_name}</td><td><span className="chip primary">{c.count}</span></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Members by Referrer Table */}
      {byReferrer?.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><h3>Miembros por Referidor</h3></div>
          <table className="data-table">
            <thead><tr><th>Referido por</th><th>Cantidad</th></tr></thead>
            <tbody>
              {byReferrer.slice(0, 15).map((r, i) => (
                <tr key={i}><td>{r.referred_by || 'Sin referencia'}</td><td><span className="chip success">{r.count}</span></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
