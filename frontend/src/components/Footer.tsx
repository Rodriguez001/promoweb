// @ts-nocheck - Bypassing React 18/19 type conflicts with HeartIcon, PhoneIcon, EnvelopeIcon, MapPinIcon
import Link from 'next/link'
import { HeartIcon, PhoneIcon, EnvelopeIcon, MapPinIcon } from '@heroicons/react/24/solid'

export function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-2 rounded-lg">
                <HeartIcon className="h-6 w-6" />
              </div>
              <span className="text-xl font-bold">PromoWeb Africa</span>
            </div>
            <p className="text-gray-300 text-sm">
              Votre plateforme de confiance pour les produits européens de qualité au Cameroun.
              Parapharmacie, beauté, bien-être et livres.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <span className="sr-only">Facebook</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <span className="sr-only">Instagram</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 6.62 5.367 11.987 11.988 11.987 6.62 0 11.987-5.367 11.987-11.987C24.014 5.367 18.637.001 12.017.001zM8.449 16.988c-1.297 0-2.448-.49-3.323-1.297C3.85 14.724 3.85 12.78 5.126 11.504s3.22-1.275 4.497 0 1.275 3.22 0 4.497c-.875.807-2.026 1.297-3.323 1.297-.49 0-.98-.122-1.42-.367z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <span className="sr-only">WhatsApp</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.465 3.488"/>
                </svg>
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Liens Rapides</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/produits" className="text-gray-300 hover:text-white transition-colors">Tous les Produits</Link></li>
              <li><Link href="/parapharmacie" className="text-gray-300 hover:text-white transition-colors">Parapharmacie</Link></li>
              <li><Link href="/beaute" className="text-gray-300 hover:text-white transition-colors">Beauté</Link></li>
              <li><Link href="/bien-etre" className="text-gray-300 hover:text-white transition-colors">Bien-être</Link></li>
              <li><Link href="/livres" className="text-gray-300 hover:text-white transition-colors">Livres</Link></li>
              <li><Link href="/promotions" className="text-gray-300 hover:text-white transition-colors">Promotions</Link></li>
            </ul>
          </div>

          {/* Customer Service */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Service Client</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/aide" className="text-gray-300 hover:text-white transition-colors">Centre d'Aide</Link></li>
              <li><Link href="/livraison" className="text-gray-300 hover:text-white transition-colors">Livraison</Link></li>
              <li><Link href="/retours" className="text-gray-300 hover:text-white transition-colors">Retours</Link></li>
              <li><Link href="/paiement" className="text-gray-300 hover:text-white transition-colors">Paiement</Link></li>
              <li><Link href="/suivi" className="text-gray-300 hover:text-white transition-colors">Suivi Commande</Link></li>
              <li><Link href="/faq" className="text-gray-300 hover:text-white transition-colors">FAQ</Link></li>
            </ul>
          </div>

          {/* Contact Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Contact</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center space-x-2">
                <MapPinIcon className="h-5 w-5 text-blue-400" />
                <span className="text-gray-300">Douala, Cameroun</span>
              </div>
              <div className="flex items-center space-x-2">
                <PhoneIcon className="h-5 w-5 text-green-400" />
                <span className="text-gray-300">+237 6XX XXX XXX</span>
              </div>
              <div className="flex items-center space-x-2">
                <EnvelopeIcon className="h-5 w-5 text-red-400" />
                <span className="text-gray-300">contact@promoweb-africa.com</span>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <h4 className="font-semibold text-sm mb-2">Horaires</h4>
              <p className="text-xs text-gray-300">Lun - Ven: 8h - 18h</p>
              <p className="text-xs text-gray-300">Sam: 9h - 15h</p>
              <p className="text-xs text-gray-300">Dim: Fermé</p>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-800 mt-8 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-sm text-gray-400 mb-4 md:mb-0">
              © 2024 PromoWeb Africa. Tous droits réservés.
            </div>
            <div className="flex space-x-6 text-sm">
              <Link href="/confidentialite" className="text-gray-400 hover:text-white transition-colors">
                Confidentialité
              </Link>
              <Link href="/conditions" className="text-gray-400 hover:text-white transition-colors">
                Conditions d'utilisation
              </Link>
              <Link href="/cookies" className="text-gray-400 hover:text-white transition-colors">
                Cookies
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
