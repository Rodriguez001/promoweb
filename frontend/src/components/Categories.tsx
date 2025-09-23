
import Link from 'next/link'
import React from 'react'

const categories = [
  {
    id: 'parapharmacie',
    name: 'Parapharmacie',
    description: 'Produits de santé et hygiène',
    icon: '🏥',
    color: 'from-blue-500 to-cyan-500',
    count: '250+ produits'
  },
  {
    id: 'beaute',
    name: 'Beauté',
    description: 'Cosmétiques et soins',
    icon: '💄',
    color: 'from-pink-500 to-rose-500',
    count: '180+ produits'
  },
  {
    id: 'bien-etre',
    name: 'Bien-être',
    description: 'Compléments et vitamines',
    icon: '🧘',
    color: 'from-green-500 to-emerald-500',
    count: '120+ produits'
  },
  {
    id: 'livres',
    name: 'Livres',
    description: 'Éducation et développement',
    icon: '📚',
    color: 'from-purple-500 to-indigo-500',
    count: '450+ livres'
  }
]

export function Categories() {
  return (
    <section className="py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
            Nos Catégories
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Explorez notre large gamme de produits européens de qualité, 
            soigneusement sélectionnés pour répondre à vos besoins.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {categories.map((category) => (
            <Link
              key={category.id}
              href={`/categories/${category.id}`}
              className="group relative bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${category.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}></div>
              
              <div className="relative p-6 text-center">
                <div className="text-4xl mb-4 transform group-hover:scale-110 transition-transform duration-300">
                  {category.icon}
                </div>
                
                <h3 className="text-xl font-semibold text-gray-900 mb-2 group-hover:text-gray-700">
                  {category.name}
                </h3>
                
                <p className="text-gray-600 text-sm mb-3">
                  {category.description}
                </p>
                
                <div className={`inline-block px-3 py-1 rounded-full text-xs font-medium text-white bg-gradient-to-r ${category.color}`}>
                  {category.count}
                </div>
              </div>
              
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-gray-200 to-transparent group-hover:via-gray-400 transition-colors duration-300"></div>
            </Link>
          ))}
        </div>

        {/* View All Categories Button */}
        <div className="text-center mt-12">
          <Link
            href="/categories"
            className="inline-flex items-center px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:border-blue-600 hover:text-blue-600 transition-all duration-200"
          >
            Voir Toutes les Catégories
            <svg className="ml-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  )
}
