/**
 * Map Page - Attendance Geolocation
 */
import { useQuery } from '@tanstack/react-query'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import api from '../services/api'

// Fix default marker icon issue
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const DEFAULT_CENTER = [23.6345, -102.5528] // Mexico center
const DEFAULT_ZOOM = 5

export default function MapPage() {
  const { data: mapData, isLoading } = useQuery({
    queryKey: ['attendance-map'],
    queryFn: () => api.get('/dashboard/attendance/map-data').then(r => r.data),
  })

  if (isLoading) return <div className="loading"><div className="spinner"></div></div>

  const markers = (mapData || []).filter(m => m.latitude && m.longitude)

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Mapa de Asistencia</h1>

      <div className="card" style={{ marginBottom: 16, padding: 12 }}>
        <span style={{ color: '#666' }}>
          {markers.length} registro{markers.length !== 1 ? 's' : ''} con ubicación geográfica
        </span>
      </div>

      <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
        <MapContainer
          center={DEFAULT_CENTER}
          zoom={DEFAULT_ZOOM}
          style={{ height: 'calc(100vh - 220px)', minHeight: 400, width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {markers.map((m, i) => (
            <Marker key={i} position={[m.latitude, m.longitude]}>
              <Popup>
                <strong>{m.full_name || m.email}</strong><br />
                {m.event_name && <><small>Evento: {m.event_name}</small><br /></>}
                {m.registered_at && <small>{new Date(m.registered_at).toLocaleString()}</small>}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}
