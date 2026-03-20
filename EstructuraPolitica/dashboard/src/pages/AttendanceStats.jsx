/**
 * Attendance Statistics Page
 */
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import api from '../services/api'

export default function AttendanceStats() {
  const { data: byEvent, isLoading } = useQuery({
    queryKey: ['attendance-by-event'],
    queryFn: () => api.get('/dashboard/attendance/by-event').then(r => r.data),
  })

  if (isLoading) return <div className="loading"><div className="spinner"></div></div>

  const chartData = (byEvent || []).slice(0, 12).map(ev => ({
    name: ev.event_name?.length > 20 ? ev.event_name.slice(0, 18) + '…' : ev.event_name,
    asistentes: ev.count,
  }))

  const totalAttendees = (byEvent || []).reduce((s, e) => s + e.count, 0)
  const totalEvents = (byEvent || []).length
  const avgAttendance = totalEvents ? (totalAttendees / totalEvents).toFixed(1) : 0

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Estadísticas de Asistencia</h1>

      {/* Summary Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{totalEvents}</div>
          <div className="stat-label">Eventos</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{totalAttendees}</div>
          <div className="stat-label">Total Asistentes</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{avgAttendance}</div>
          <div className="stat-label">Promedio por Evento</div>
        </div>
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="card chart-card" style={{ marginBottom: 24 }}>
          <div className="card-header"><h3>Asistencia por Evento</h3></div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-30} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="asistentes" fill="#2e7d32" name="Asistentes" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Events Table */}
      <div className="card">
        <div className="card-header"><h3>Detalle de Eventos</h3></div>
        {byEvent?.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Evento</th>
                <th>Asistentes</th>
              </tr>
            </thead>
            <tbody>
              {byEvent.map((ev, i) => (
                <tr key={i}>
                  <td>{ev.event_name}</td>
                  <td><span className="chip primary">{ev.count}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ textAlign: 'center', color: '#999', padding: 40 }}>
            No hay eventos registrados aún.
          </p>
        )}
      </div>
    </div>
  )
}
