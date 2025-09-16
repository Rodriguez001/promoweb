import { TruckIcon, CreditCardIcon, ShieldCheckIcon, PhoneIcon, ClockIcon, GlobeAltIcon } from '@heroicons/react/24/outline'

const features = [
  {
    icon: TruckIcon,
    title: 'Livraison Rapide',
    description: 'Recevez vos produits en 5 à 10 jours ouvrables partout au Cameroun',
    color: 'text-blue-600'
  },
  {
    icon: CreditCardIcon,
    title: 'Paiement Flexible',
    description: 'Acompte à la commande, solde à la livraison. Mobile Money et cartes acceptées',
    color: 'text-green-600'
  },
  {
    icon: ShieldCheckIcon,
    title: 'Qualité Garantie',
    description: 'Produits européens authentiques avec garantie de qualité et de fraîcheur',
    color: 'text-purple-600'
  },
  {
    icon: PhoneIcon,
    title: 'Support Client',
    description: 'Équipe dédiée disponible pour vous accompagner dans vos achats',
    color: 'text-red-600'
  },
  {
    icon: ClockIcon,
    title: 'Suivi en Temps Réel',
    description: 'Suivez votre commande étape par étape jusqu\'à la livraison',
    color: 'text-yellow-600'
  },
  {
    icon: GlobeAltIcon,
    title: 'Catalogue Actualisé',
    description: 'Plus de 1000 produits mis à jour quotidiennement depuis l\'Europe',
    color: 'text-indigo-600'
  }
]

export function Features() {
  return (
    <section className="py-16 bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
            Pourquoi Choisir PromoWeb Africa ?
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Nous nous engageons à vous offrir la meilleure expérience d'achat 
            de produits européens au Cameroun avec des services de qualité.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="group relative bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100"
            >
              <div className="flex items-start space-x-4">
                <div className={`flex-shrink-0 p-3 rounded-lg bg-gray-50 group-hover:bg-gray-100 transition-colors duration-300`}>
                  <feature.icon className={`h-6 w-6 ${feature.color}`} />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-gray-700">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
              
              {/* Hover effect border */}
              <div className="absolute inset-0 rounded-xl border-2 border-transparent group-hover:border-gray-200 transition-colors duration-300"></div>
            </div>
          ))}
        </div>

        {/* Call to Action */}
        <div className="text-center mt-12">
          <div className="bg-white rounded-2xl shadow-lg p-8 max-w-2xl mx-auto">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Prêt à Commencer ?
            </h3>
            <p className="text-gray-600 mb-6">
              Rejoignez des centaines de clients satisfaits qui font confiance à PromoWeb Africa 
              pour leurs achats de produits européens.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="/inscription"
                className="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-blue-600 to-green-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-green-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Créer un Compte
              </a>
              <a
                href="/contact"
                className="inline-flex items-center justify-center px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:border-blue-600 hover:text-blue-600 transition-all duration-200"
              >
                Nous Contacter
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
