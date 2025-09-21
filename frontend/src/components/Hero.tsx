// @ts-nocheck - Bypassing React 18/19 type conflicts with ChevronRightIcon, TruckIcon, CreditCardIcon, ShieldCheckIcon
'use client'

import Link from 'next/link'
import { ChevronRightIcon, TruckIcon, CreditCardIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'

export function Hero() {
  return (
    <div className="relative bg-gradient-to-br from-blue-50 via-white to-green-50 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <div className="space-y-8">
            <div className="space-y-4">
              <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 leading-tight">
                Produits Européens
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-green-600">
                  {' '}de Qualité
                </span>
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                Découvrez notre sélection exclusive de produits de parapharmacie, beauté, 
                bien-être et livres européens, livrés directement au Cameroun.
              </p>
            </div>

            {/* Key Benefits */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <TruckIcon className="h-5 w-5 text-blue-600" />
                <span>Livraison 5-10 jours</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <CreditCardIcon className="h-5 w-5 text-green-600" />
                <span>Paiement flexible</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <ShieldCheckIcon className="h-5 w-5 text-purple-600" />
                <span>Qualité garantie</span>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Link 
                href="/produits"
                className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-blue-600 to-green-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-green-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Découvrir les Produits
                <ChevronRightIcon className="ml-2 h-5 w-5" />
              </Link>
              <Link 
                href="/categories"
                className="inline-flex items-center justify-center px-8 py-4 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:border-blue-600 hover:text-blue-600 transition-all duration-200"
              >
                Voir les Catégories
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 pt-8 border-t border-gray-200">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">1000+</div>
                <div className="text-sm text-gray-600">Produits</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">500+</div>
                <div className="text-sm text-gray-600">Clients Satisfaits</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">98%</div>
                <div className="text-sm text-gray-600">Satisfaction</div>
              </div>
            </div>
          </div>

          {/* Hero Image */}
          <div className="relative">
            <div className="relative z-10 bg-white rounded-2xl shadow-2xl p-8">
              <div className="grid grid-cols-2 gap-4">
                {/* Product Cards */}
                <div className="bg-gradient-to-br from-pink-50 to-purple-50 rounded-lg p-4 text-center">
                  <div className="w-16 h-16 bg-pink-200 rounded-full mx-auto mb-3 flex items-center justify-center">
                    <span className="text-2xl">💄</span>
                  </div>
                  <h3 className="font-semibold text-gray-900 text-sm">Beauté</h3>
                  <p className="text-xs text-gray-600 mt-1">Cosmétiques européens</p>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg p-4 text-center">
                  <div className="w-16 h-16 bg-green-200 rounded-full mx-auto mb-3 flex items-center justify-center">
                    <span className="text-2xl">🏥</span>
                  </div>
                  <h3 className="font-semibold text-gray-900 text-sm">Parapharmacie</h3>
                  <p className="text-xs text-gray-600 mt-1">Produits de santé</p>
                </div>
                
                <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-lg p-4 text-center">
                  <div className="w-16 h-16 bg-yellow-200 rounded-full mx-auto mb-3 flex items-center justify-center">
                    <span className="text-2xl">🧘</span>
                  </div>
                  <h3 className="font-semibold text-gray-900 text-sm">Bien-être</h3>
                  <p className="text-xs text-gray-600 mt-1">Compléments naturels</p>
                </div>
                
                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-4 text-center">
                  <div className="w-16 h-16 bg-indigo-200 rounded-full mx-auto mb-3 flex items-center justify-center">
                    <span className="text-2xl">📚</span>
                  </div>
                  <h3 className="font-semibold text-gray-900 text-sm">Livres</h3>
                  <p className="text-xs text-gray-600 mt-1">Éducation & Culture</p>
                </div>
              </div>
              
              {/* Special Offer Badge */}
              <div className="absolute -top-4 -right-4 bg-red-500 text-white px-4 py-2 rounded-full text-sm font-bold transform rotate-12 shadow-lg">
                -20% 🎉
              </div>
            </div>
            
            {/* Background Decorations */}
            <div className="absolute top-4 left-4 w-24 h-24 bg-blue-200 rounded-full opacity-20 animate-pulse"></div>
            <div className="absolute bottom-8 right-8 w-32 h-32 bg-green-200 rounded-full opacity-20 animate-pulse delay-1000"></div>
          </div>
        </div>
      </div>
    </div>
  )
}
