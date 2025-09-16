'use client'

import { useState } from 'react'
import Link from 'next/link'
import { StarIcon, HeartIcon, ShoppingCartIcon } from '@heroicons/react/24/solid'
import { HeartIcon as HeartOutlineIcon } from '@heroicons/react/24/outline'

// Mock data for featured products
const featuredProducts = [
  {
    id: 1,
    name: 'Crème Hydratante Bio',
    brand: 'L\'Occitane',
    price: 15500,
    originalPrice: 18500,
    currency: 'XAF',
    image: '/api/placeholder/300/300',
    rating: 4.8,
    reviews: 124,
    category: 'Beauté',
    isNew: true,
    discount: 16
  },
  {
    id: 2,
    name: 'Vitamine D3 + K2',
    brand: 'Solgar',
    price: 12800,
    originalPrice: null,
    currency: 'XAF',
    image: '/api/placeholder/300/300',
    rating: 4.9,
    reviews: 89,
    category: 'Bien-être',
    isNew: false,
    discount: 0
  },
  {
    id: 3,
    name: 'Shampoing Anti-Chute',
    brand: 'Klorane',
    price: 8900,
    originalPrice: 11200,
    currency: 'XAF',
    image: '/api/placeholder/300/300',
    rating: 4.6,
    reviews: 156,
    category: 'Parapharmacie',
    isNew: false,
    discount: 21
  },
  {
    id: 4,
    name: 'Le Petit Prince',
    brand: 'Gallimard',
    price: 4500,
    originalPrice: null,
    currency: 'XAF',
    image: '/api/placeholder/300/300',
    rating: 4.9,
    reviews: 203,
    category: 'Livres',
    isNew: false,
    discount: 0
  }
]

export function FeaturedProducts() {
  const [favorites, setFavorites] = useState<number[]>([])

  const toggleFavorite = (productId: number) => {
    setFavorites(prev => 
      prev.includes(productId) 
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    )
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR').format(price)
  }

  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
            Produits Vedettes
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Découvrez notre sélection de produits les plus populaires, 
            choisis par nos clients camerounais.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredProducts.map((product) => (
            <div
              key={product.id}
              className="group relative bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100"
            >
              {/* Product Image */}
              <div className="relative aspect-square overflow-hidden bg-gray-100">
                <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                  <span className="text-4xl opacity-50">📦</span>
                </div>
                
                {/* Badges */}
                <div className="absolute top-3 left-3 flex flex-col gap-2">
                  {product.isNew && (
                    <span className="bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                      Nouveau
                    </span>
                  )}
                  {product.discount > 0 && (
                    <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                      -{product.discount}%
                    </span>
                  )}
                </div>

                {/* Favorite Button */}
                <button
                  onClick={() => toggleFavorite(product.id)}
                  className="absolute top-3 right-3 p-2 bg-white rounded-full shadow-md hover:shadow-lg transition-all duration-200"
                >
                  {favorites.includes(product.id) ? (
                    <HeartIcon className="h-5 w-5 text-red-500" />
                  ) : (
                    <HeartOutlineIcon className="h-5 w-5 text-gray-400 hover:text-red-500" />
                  )}
                </button>

                {/* Quick Actions */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex gap-2">
                    <Link
                      href={`/produits/${product.id}`}
                      className="bg-white text-gray-900 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors duration-200"
                    >
                      Voir Détails
                    </Link>
                  </div>
                </div>
              </div>

              {/* Product Info */}
              <div className="p-4">
                <div className="mb-2">
                  <span className="text-xs text-blue-600 font-medium bg-blue-50 px-2 py-1 rounded">
                    {product.category}
                  </span>
                </div>
                
                <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">
                  {product.name}
                </h3>
                
                <p className="text-sm text-gray-600 mb-2">
                  {product.brand}
                </p>

                {/* Rating */}
                <div className="flex items-center gap-1 mb-3">
                  <div className="flex">
                    {[...Array(5)].map((_, i) => (
                      <StarIcon
                        key={i}
                        className={`h-4 w-4 ${
                          i < Math.floor(product.rating)
                            ? 'text-yellow-400'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-sm text-gray-600">
                    {product.rating} ({product.reviews})
                  </span>
                </div>

                {/* Price */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold text-gray-900">
                      {formatPrice(product.price)} {product.currency}
                    </span>
                    {product.originalPrice && (
                      <span className="text-sm text-gray-500 line-through">
                        {formatPrice(product.originalPrice)} {product.currency}
                      </span>
                    )}
                  </div>
                </div>

                {/* Add to Cart Button */}
                <button className="w-full bg-gradient-to-r from-blue-600 to-green-600 text-white py-2 px-4 rounded-lg font-medium hover:from-blue-700 hover:to-green-700 transition-all duration-200 flex items-center justify-center gap-2">
                  <ShoppingCartIcon className="h-4 w-4" />
                  Ajouter au Panier
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* View All Products Button */}
        <div className="text-center mt-12">
          <Link
            href="/produits"
            className="inline-flex items-center px-8 py-3 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-all duration-200"
          >
            Voir Tous les Produits
            <svg className="ml-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  )
}
