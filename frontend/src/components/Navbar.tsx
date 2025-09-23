// @ts-nocheck 
'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ShoppingCartIcon, UserIcon, MagnifyingGlassIcon, Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'
import { HeartIcon } from '@heroicons/react/24/solid'

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-2 rounded-lg">
              <HeartIcon className="h-6 w-6" />
            </div>
            <span className="text-xl font-bold text-gray-900">PromoWeb Africa</span>
          </Link>

          {/* Search Bar - Desktop */}
          <div className="hidden md:flex flex-1 max-w-lg mx-8">
            <div className="relative w-full">
              <input
                type="text"
                placeholder="Rechercher des produits..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          {/* Navigation Links - Desktop */}
          <div className="hidden md:flex items-center space-x-6">
            <Link href="/produits" className="text-gray-700 hover:text-blue-600 font-medium">
              Produits
            </Link>
            <Link href="/categories" className="text-gray-700 hover:text-blue-600 font-medium">
              Catégories
            </Link>
            <Link href="/contact" className="text-gray-700 hover:text-blue-600 font-medium">
              Contact
            </Link>
            
            {/* User Actions */}
            <div className="flex items-center space-x-4">
              <Link href="/compte" className="text-gray-700 hover:text-blue-600">
                <UserIcon className="h-6 w-6" />
              </Link>
              <Link href="/panier" className="relative text-gray-700 hover:text-blue-600">
                <ShoppingCartIcon className="h-6 w-6" />
                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  0
                </span>
              </Link>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-700 hover:text-blue-600"
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-50 rounded-lg mt-2">
              {/* Mobile Search */}
              <div className="relative mb-4">
                <input
                  type="text"
                  placeholder="Rechercher des produits..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              </div>
              
              <Link href="/produits" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">
                Produits
              </Link>
              <Link href="/categories" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">
                Catégories
              </Link>
              <Link href="/contact" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">
                Contact
              </Link>
              <Link href="/compte" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">
                Mon Compte
              </Link>
              <Link href="/panier" className="block px-3 py-2 text-gray-700 hover:text-blue-600 font-medium">
                Panier (0)
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
