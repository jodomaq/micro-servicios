import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-600 via-brand-500 to-pink-500 text-white">
        <div className="max-w-6xl mx-auto px-4 py-20 md:py-32 text-center">
          <h1 className="text-4xl md:text-6xl font-extrabold leading-tight">
            Tu mesa de regalos
            <br />
            <span className="text-yellow-300">digital</span> 🎁
          </h1>
          <p className="mt-6 text-lg md:text-xl text-white/90 max-w-2xl mx-auto">
            Crea tu wishlist con productos en línea, compártela con
            familia y amigos, y recibe exactamente lo que quieres.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to={user ? "/dashboard" : "/registro"}
              className="bg-cta hover:bg-cta-hover text-gray-900 font-bold px-8 py-4 rounded-2xl text-lg transition-colors shadow-lg"
            >
              {user ? "Ir a mis mesas" : "Crear mi mesa gratis"}
            </Link>
            <a
              href="#como-funciona"
              className="border-2 border-white/40 hover:border-white text-white font-semibold px-8 py-4 rounded-2xl text-lg transition-colors"
            >
              ¿Cómo funciona?
            </a>
          </div>
        </div>
      </section>

      {/* Cómo funciona */}
      <section id="como-funciona" className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-gray-900">
            Así de fácil es usar Mesa de Regalos
          </h2>
          <div className="mt-14 grid md:grid-cols-3 gap-10">
            {[
              {
                icon: "📝",
                title: "Crea tu mesa",
                desc: "Regístrate gratis y crea una mesa de regalos para tu cumpleaños, boda, baby shower o lo que quieras.",
              },
              {
                icon: "🛒",
                title: "Añade productos",
                desc: "Pega el enlace de cualquier producto de Mercado Libre y nosotros extraemos la info automáticamente.",
              },
              {
                icon: "🔗",
                title: "Comparte tu link",
                desc: "Envía tu mesa a familia y amigos. Ellos ven los regalos y compran directamente en Mercado Libre.",
              },
            ].map((step, i) => (
              <div
                key={i}
                className="text-center p-8 rounded-2xl bg-gray-50 hover:bg-brand-50 transition-colors"
              >
                <div className="text-5xl mb-4">{step.icon}</div>
                <h3 className="text-xl font-bold text-gray-900">{step.title}</h3>
                <p className="mt-3 text-gray-600 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Beneficios */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-gray-900">
            ¿Por qué elegir Mesa de Regalos?
          </h2>
          <div className="mt-14 grid md:grid-cols-2 gap-8">
            {[
              {
                icon: "🎯",
                title: "Recibe lo que realmente quieres",
                desc: "Nada de regalos repetidos o que no te gustan. Tú eliges exactamente lo que deseas.",
              },
              {
                icon: "📱",
                title: "Fácil de usar desde el celular",
                desc: "Diseñada para que cualquier persona pueda usarla, sin complicaciones.",
              },
              {
                icon: "🛡️",
                title: "Compras seguras en Mercado Libre",
                desc: "Tus invitados compran con la protección y garantía de Mercado Libre.",
              },
              {
                icon: "⭐",
                title: "Premium para más funciones",
                desc: "Desbloquea mesas ilimitadas, diseños personalizados y más con Premium.",
              },
            ].map((item, i) => (
              <div
                key={i}
                className="flex gap-4 p-6 rounded-2xl bg-white shadow-sm hover:shadow-md transition-shadow"
              >
                <span className="text-4xl flex-shrink-0">{item.icon}</span>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    {item.title}
                  </h3>
                  <p className="mt-1 text-gray-600">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA final */}
      <section className="py-20 bg-brand-600 text-white text-center">
        <div className="max-w-3xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold">
            ¿Listo para crear tu mesa?
          </h2>
          <p className="mt-4 text-lg text-white/90">
            Es gratis, rápido y tus invitados te lo van a agradecer.
          </p>
          <Link
            to={user ? "/dashboard" : "/registro"}
            className="mt-8 inline-block bg-cta hover:bg-cta-hover text-gray-900 font-bold px-10 py-4 rounded-2xl text-lg transition-colors shadow-lg"
          >
            {user ? "Ir a mis mesas" : "Empezar ahora"}
          </Link>
        </div>
      </section>
    </>
  );
}
