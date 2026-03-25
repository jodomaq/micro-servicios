/**
 * Navegador de Secciones Electorales con mapa de polígonos.
 *
 * Filtros jerárquicos: Estado → Municipio → Distrito → Sección.
 * El tenant puede tener secciones de cualquier estado de la república;
 * el selector de estado es el punto de entrada para acotar la búsqueda.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './SeccionesMapPage.css'
import api from '../services/api'

// ── Subcomponente: vuela al bounds/centro cuando cambia el target ──────────
function MapFlyTo({ target }) {
  const map = useMap()
  useEffect(() => {
    if (!target) return
    if (target.bounds) {
      map.flyToBounds(target.bounds, { padding: [30, 30], maxZoom: 15, duration: 0.8 })
    } else if (target.center) {
      map.flyTo(target.center, 14, { duration: 0.8 })
    }
  }, [target, map])
  return null
}

// ── Paleta de colores para polígonos ──────────────────────────────────────
const PALETTE = [
  '#e63946', '#457b9d', '#2a9d8f', '#e9c46a', '#f4a261',
  '#264653', '#6a4c93', '#1982c4', '#8ac926', '#ff595e',
  '#6a994e', '#bc4749', '#0077b6', '#f77f00', '#7209b7',
  '#3a86ff', '#fb5607', '#38b000', '#9b2226', '#0096c7',
]
const colorFor = (n) => PALETTE[(n ?? 0) % PALETTE.length]

// ── Componente principal ──────────────────────────────────────────────────
export default function SeccionesMapPage() {
  // Catálogos
  const [estados, setEstados] = useState([])
  const [municipios, setMunicipios] = useState([])
  const [distritos, setDistritos] = useState([])

  // Secciones con polígono
  const [secciones, setSecciones] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Filtros seleccionados
  const [filterEstado, setFilterEstado] = useState('')
  const [filterMunicipio, setFilterMunicipio] = useState('')
  const [filterDistrito, setFilterDistrito] = useState('')
  const [filterSeccion, setFilterSeccion] = useState('')

  // Sección resaltada y vuelo del mapa
  const [selectedSeccion, setSelectedSeccion] = useState(null)
  const [mapTarget, setMapTarget] = useState(null)
  const geoJsonKey = useRef(0)

  // ── Cargar catálogos al montar ─────────────────────────────────────────
  useEffect(() => {
    Promise.all([
      api.get('/secciones/estados'),
      api.get('/secciones/municipios'),
      api.get('/secciones/distritos'),
    ]).then(([eRes, mRes, dRes]) => {
      setEstados(eRes.data)
      setMunicipios(mRes.data)
      setDistritos(dRes.data)
    }).catch(() => {})
  }, [])

  // ── Cargar polígonos según filtros activos ─────────────────────────────
  const loadPoligonos = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {}
      if (filterEstado)    params.estado_id    = filterEstado
      if (filterMunicipio) params.municipio_id = filterMunicipio
      if (filterDistrito)  params.distrito_id  = filterDistrito

      const res = await api.get('/secciones/poligonos', { params })
      setSecciones(res.data)
      geoJsonKey.current += 1

      // Zoom automático al conjunto de secciones cargadas
      if (res.data.length > 0) {
        const withBbox = res.data.filter(s => s.bbox)
        if (withBbox.length > 0) {
          const lats = withBbox.flatMap(s => [s.bbox.min_lat, s.bbox.max_lat])
          const lons = withBbox.flatMap(s => [s.bbox.min_lon, s.bbox.max_lon])
          setMapTarget({
            bounds: [
              [Math.min(...lats), Math.min(...lons)],
              [Math.max(...lats), Math.max(...lons)],
            ],
          })
        }
      }
    } catch {
      setError('No se pudieron cargar las secciones.')
    } finally {
      setLoading(false)
    }
  }, [filterEstado, filterMunicipio, filterDistrito])

  useEffect(() => { loadPoligonos() }, [loadPoligonos])

  // ── Ir a sección específica cuando se selecciona del combo ────────────
  useEffect(() => {
    if (!filterSeccion) { setSelectedSeccion(null); return }
    const sec = secciones.find(s => String(s.seccion) === filterSeccion)
    if (sec) {
      setSelectedSeccion(sec.seccion)
      if (sec.bbox) {
        setMapTarget({
          bounds: [
            [sec.bbox.min_lat, sec.bbox.min_lon],
            [sec.bbox.max_lat, sec.bbox.max_lon],
          ],
        })
      }
    }
  }, [filterSeccion, secciones])

  // ── Secciones disponibles en el select ────────────────────────────────
  const seccionesDisponibles = [...new Set(secciones.map(s => s.seccion))].sort((a, b) => a - b)

  // ── Municipios y distritos filtrados por estado ────────────────────────
  const municipiosFiltrados = filterEstado
    ? municipios  // El backend ya filtra por tenant; podrías refinar si tuvieras estado en el catálogo
    : municipios

  // ── Estilos de polígono ────────────────────────────────────────────────
  const getStyle = useCallback(
    (feature) => {
      const num = feature?.properties?.seccion
      const isSelected = num !== undefined && num === selectedSeccion
      const base = colorFor(num)
      return {
        color: isSelected ? '#ffffff' : base,
        weight: isSelected ? 3 : 1.5,
        fillColor: base,
        fillOpacity: isSelected ? 0.35 : 0.45,
        opacity: 1,
      }
    },
    [selectedSeccion]
  )

  // ── Interacción por clic en polígono ──────────────────────────────────
  const onEachFeature = useCallback((feature, layer) => {
    const { seccion, nombre_municipio, nombre_estado, distrito_id } = feature.properties || {}
    layer.bindPopup(
      `<b>Sección ${seccion}</b><br/>
       ${nombre_estado ?? ''}<br/>
       ${nombre_municipio ?? ''}<br/>
       ${distrito_id != null ? `Distrito local ${distrito_id}` : ''}`,
      { className: 'seccion-tooltip' }
    )
    layer.on('click', () => {
      setSelectedSeccion(seccion)
      setFilterSeccion(String(seccion))
      layer.openPopup()
    })
  }, [])

  // ── FeatureCollection para react-leaflet ──────────────────────────────
  const geojsonData = {
    type: 'FeatureCollection',
    features: secciones
      .filter(s => s.geojson)
      .map(s => {
        let geometry
        try {
          geometry = typeof s.geojson === 'string' ? JSON.parse(s.geojson) : s.geojson
        } catch { return null }
        return {
          type: 'Feature',
          properties: {
            seccion: s.seccion,
            nombre_estado: s.nombre_estado,
            nombre_municipio: s.nombre_municipio,
            municipio_id: s.municipio_id,
            distrito_id: s.distrito_id,
            distrito_federal: s.distrito_federal,
          },
          geometry,
        }
      })
      .filter(Boolean),
  }

  const secActual = selectedSeccion != null
    ? secciones.find(s => s.seccion === selectedSeccion)
    : null

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <div className="smn-wrapper">
      {/* Cabecera */}
      <div className="smn-header">
        <div className="smn-title-block">
          <h1 className="smn-title">Navegador de Secciones</h1>
          <p className="smn-subtitle">
            {secciones.length} secciones con polígono
            {secActual ? ` · Sección ${secActual.seccion} seleccionada` : ''}
          </p>
        </div>
      </div>

      {/* Filtros */}
      <div className="smn-filters">
        {/* Estado */}
        <div className="smn-filter-group">
          <label className="smn-label">Estado</label>
          <select
            className="smn-select"
            value={filterEstado}
            onChange={e => {
              setFilterEstado(e.target.value)
              setFilterMunicipio('')
              setFilterDistrito('')
              setFilterSeccion('')
              setSelectedSeccion(null)
            }}
          >
            <option value="">Todos los estados</option>
            {estados.map(e => (
              <option key={e.estado_id} value={e.estado_id}>
                {e.nombre_estado}
              </option>
            ))}
          </select>
        </div>

        {/* Municipio */}
        <div className="smn-filter-group">
          <label className="smn-label">Municipio</label>
          <select
            className="smn-select"
            value={filterMunicipio}
            onChange={e => {
              setFilterMunicipio(e.target.value)
              setFilterDistrito('')
              setFilterSeccion('')
              setSelectedSeccion(null)
            }}
          >
            <option value="">Todos los municipios</option>
            {municipiosFiltrados.map(m => (
              <option key={m.municipio_id} value={m.municipio_id}>
                {m.nombre}
              </option>
            ))}
          </select>
        </div>

        {/* Distrito local */}
        <div className="smn-filter-group">
          <label className="smn-label">Distrito local</label>
          <select
            className="smn-select"
            value={filterDistrito}
            onChange={e => {
              setFilterDistrito(e.target.value)
              setFilterSeccion('')
              setSelectedSeccion(null)
            }}
          >
            <option value="">Todos los distritos</option>
            {distritos.map(d => (
              <option key={d.distrito_id} value={d.distrito_id}>
                Distrito {d.nombre || d.distrito_id}
              </option>
            ))}
          </select>
        </div>

        {/* Sección */}
        <div className="smn-filter-group">
          <label className="smn-label">Sección</label>
          <select
            className="smn-select"
            value={filterSeccion}
            onChange={e => setFilterSeccion(e.target.value)}
          >
            <option value="">Selecciona sección…</option>
            {seccionesDisponibles.map(sec => (
              <option key={sec} value={sec}>Sección {sec}</option>
            ))}
          </select>
        </div>

        {/* Limpiar */}
        {(filterEstado || filterMunicipio || filterDistrito || filterSeccion) && (
          <button
            className="smn-clear-btn"
            type="button"
            onClick={() => {
              setFilterEstado('')
              setFilterMunicipio('')
              setFilterDistrito('')
              setFilterSeccion('')
              setSelectedSeccion(null)
            }}
          >
            Limpiar filtros
          </button>
        )}

        {loading && <span className="smn-loading">Cargando…</span>}
        {error && <span className="smn-error">{error}</span>}
      </div>

      {/* Info sección seleccionada */}
      {secActual && (
        <div className="smn-info-bar">
          <span className="smn-info-badge">Sección {secActual.seccion}</span>
          {secActual.nombre_estado && <span>{secActual.nombre_estado}</span>}
          {secActual.nombre_municipio && <span>{secActual.nombre_municipio}</span>}
          {secActual.distrito_id && <span>Distrito local {secActual.distrito_id}</span>}
          {secActual.distrito_federal && <span>Distrito federal {secActual.distrito_federal}</span>}
        </div>
      )}

      {/* Mapa */}
      <div className="smn-map-container">
        <MapContainer
          center={[23.6345, -102.5528]}
          zoom={5}
          className="smn-map"
          zoomControl
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />

          {geojsonData.features.length > 0 && (
            <GeoJSON
              key={`${geoJsonKey.current}-${selectedSeccion}`}
              data={geojsonData}
              style={getStyle}
              onEachFeature={onEachFeature}
            />
          )}

          <MapFlyTo target={mapTarget} />
        </MapContainer>
      </div>
    </div>
  )
}
