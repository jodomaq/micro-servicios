import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      {/* Encabezado */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-10">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            ¡Hola, {user?.name || "amigo"}! 👋
          </h1>
          <p className="mt-1 text-gray-600">
            Aquí están tus mesas de regalos
          </p>
        </div>
        <button className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors flex items-center gap-2 self-start">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Crear nueva mesa
        </button>
      </div>

      {/* Estado Premium */}
      {!user?.is_premium && (
        <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200 rounded-2xl p-6 mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              ⭐ Hazte Premium
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Desbloquea mesas ilimitadas, diseños personalizados y mucho más.
            </p>
          </div>
          <button className="bg-cta hover:bg-cta-hover text-gray-900 font-bold px-6 py-2.5 rounded-xl transition-colors whitespace-nowrap">
            Suscribirme
          </button>
        </div>
      )}

      {/* Estado vacío */}
      <div className="text-center py-20">
        <div className="text-6xl mb-6">📦</div>
        <h2 className="text-2xl font-bold text-gray-900">
          Aún no tienes mesas de regalos
        </h2>
        <p className="mt-3 text-gray-600 max-w-md mx-auto">
          Crea tu primera mesa, agrega productos de Mercado Libre y
          compártela con tus seres queridos.
        </p>
        <button className="mt-8 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-8 py-3 rounded-xl transition-colors inline-flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Crear mi primera mesa
        </button>
      </div>
    </div>
  );
}
