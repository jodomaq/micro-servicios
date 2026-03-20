import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <span className="text-2xl">🎁</span>
          <span className="font-bold text-xl text-gray-900">
            Mesa de Regalos
          </span>
        </Link>

        {/* Desktop menu */}
        <div className="hidden md:flex items-center gap-4">
          {user ? (
            <>
              <Link
                to="/dashboard"
                className="text-gray-600 hover:text-brand-600 font-medium transition-colors"
              >
                Mis mesas
              </Link>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  {user.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt={user.name}
                      className="w-8 h-8 rounded-full"
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-bold">
                      {(user.name || user.email)[0].toUpperCase()}
                    </div>
                  )}
                  <span className="text-sm text-gray-700 font-medium">
                    {user.name || user.email.split("@")[0]}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-500 hover:text-red-500 transition-colors"
                >
                  Cerrar sesión
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-gray-600 hover:text-brand-600 font-medium transition-colors"
              >
                Iniciar sesión
              </Link>
              <Link
                to="/registro"
                className="bg-brand-600 hover:bg-brand-700 text-white px-5 py-2 rounded-xl font-semibold transition-colors"
              >
                Crear cuenta
              </Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 text-gray-600"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Menú"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t bg-white px-4 py-4 space-y-3">
          {user ? (
            <>
              <div className="flex items-center gap-2 pb-2 border-b">
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={user.name}
                    className="w-8 h-8 rounded-full"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-bold">
                    {(user.name || user.email)[0].toUpperCase()}
                  </div>
                )}
                <span className="text-sm font-medium text-gray-700">
                  {user.name || user.email.split("@")[0]}
                </span>
              </div>
              <Link
                to="/dashboard"
                className="block text-gray-700 font-medium"
                onClick={() => setMenuOpen(false)}
              >
                Mis mesas
              </Link>
              <button
                onClick={() => { handleLogout(); setMenuOpen(false); }}
                className="block text-red-500 font-medium"
              >
                Cerrar sesión
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="block text-gray-700 font-medium"
                onClick={() => setMenuOpen(false)}
              >
                Iniciar sesión
              </Link>
              <Link
                to="/registro"
                className="block bg-brand-600 text-white px-4 py-2 rounded-xl font-semibold text-center"
                onClick={() => setMenuOpen(false)}
              >
                Crear cuenta
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
