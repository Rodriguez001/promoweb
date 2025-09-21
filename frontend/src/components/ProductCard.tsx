/**
 * ProductCard - Individual product display component
 * Supports both grid and list view modes
 */

'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  ShoppingCart,
  Heart,
  Star,
  Eye,
  Badge as BadgeIcon,
  Truck
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter } from '@/components/ui/card';

import { formatCurrency } from '@/lib/utils';
import { Product } from '@/types/product';

interface ProductCardProps {
  product: Product;
  viewMode: 'grid' | 'list';
  onAddToCart: (productId: string, quantity?: number) => void;
  onWishlistToggle: (productId: string) => void;
  isInWishlist?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  viewMode,
  onAddToCart,
  onWishlistToggle,
  isInWishlist = false
}) => {
  const [imageError, setImageError] = useState(false);

  // Calculate pricing
  const hasDiscount = product.discount_percentage && product.discount_percentage > 0;
  const discountedPrice = hasDiscount 
    ? product.price_xaf * (1 - product.discount_percentage! / 100)
    : product.price_xaf;

  // Rating display
  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-3 w-3 ${
          i < Math.floor(rating)
            ? 'text-yellow-400 fill-yellow-400'
            : 'text-gray-300'
        }`}
      />
    ));
  };

  // Stock status
  const isInStock = (product.inventory?.available_quantity ?? 0) > 0;

  if (viewMode === 'list') {
    return (
      <Card className="overflow-hidden hover:shadow-lg transition-shadow">
        <div className="flex">
          {/* Image */}
          <div className="relative w-48 h-48 shrink-0">
            <Link href={`/products/${product.id}`}>
              <Image
                src={product.main_image || '/placeholder-product.jpg'}
                alt={product.title}
                fill
                className="object-cover hover:scale-105 transition-transform"
                onError={() => setImageError(true)}
              />
            </Link>
          </div>

          {/* Content */}
          <div className="flex-1 p-6">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <Link href={`/products/${product.id}`}>
                  <h3 className="font-semibold text-lg hover:text-blue-600 line-clamp-2">
                    {product.title}
                  </h3>
                </Link>
                
                {product.brand && (
                  <p className="text-gray-600 text-sm mt-1">{product.brand}</p>
                )}

                <p className="text-gray-700 mt-2 line-clamp-2">{product.description}</p>

                {/* Rating */}
                {product.average_rating && (
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex">{renderStars(product.average_rating)}</div>
                    <span className="text-sm text-gray-600">
                      ({product.review_count || 0} reviews)
                    </span>
                  </div>
                )}

                {/* Price */}
                <div className="flex items-center gap-3 mt-3">
                  <span className="text-2xl font-bold text-green-600">
                    {formatCurrency(discountedPrice)}
                  </span>
                  {hasDiscount && (
                    <span className="text-lg text-gray-500 line-through">
                      {formatCurrency(product.price_xaf)}
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-col gap-2 ml-4">
                <Button
                  size="sm"
                  onClick={() => onWishlistToggle(product.id)}
                  variant={isInWishlist ? "default" : "outline"}
                >
                  <Heart className={`h-4 w-4 ${isInWishlist ? 'fill-current' : ''}`} />
                </Button>
                
                <Button
                  size="sm"
                  onClick={() => onAddToCart(product.id)}
                  disabled={!isInStock}
                  className="flex items-center gap-2"
                >
                  <ShoppingCart className="h-4 w-4" />
                  {isInStock ? 'Add to Cart' : 'Out of Stock'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // Grid view
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -5 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="group overflow-hidden hover:shadow-xl transition-all duration-300">
        {/* Image Container */}
        <div className="relative aspect-square overflow-hidden">
          <Link href={`/products/${product.id}`}>
            <Image
              src={product.main_image || '/placeholder-product.jpg'}
              alt={product.title}
              fill
              className="object-cover group-hover:scale-110 transition-transform duration-300"
              onError={() => setImageError(true)}
            />
          </Link>
          
          {/* Badges */}
          <div className="absolute top-2 left-2 flex flex-col gap-1">
            {hasDiscount && (
              <Badge variant="destructive" className="text-xs">
                -{Math.round(product.discount_percentage!)}%
              </Badge>
            )}
            {product.is_featured && (
              <Badge variant="secondary" className="text-xs">
                Featured
              </Badge>
            )}
          </div>

          {/* Quick Actions */}
          <div className="absolute top-2 right-2 flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => onWishlistToggle(product.id)}
              className="h-8 w-8 p-0"
            >
              <Heart className={`h-4 w-4 ${isInWishlist ? 'fill-current' : ''}`} />
            </Button>
            
            <Link href={`/products/${product.id}`}>
              <Button size="sm" variant="secondary" className="h-8 w-8 p-0">
                <Eye className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* Stock indicator */}
          {!isInStock && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
              <Badge variant="destructive">Out of Stock</Badge>
            </div>
          )}
        </div>

        <CardContent className="p-4">
          {/* Brand */}
          {product.brand && (
            <p className="text-xs text-gray-600 mb-1">{product.brand}</p>
          )}

          {/* Title */}
          <Link href={`/products/${product.id}`}>
            <h3 className="font-semibold text-sm hover:text-blue-600 line-clamp-2 mb-2">
              {product.title}
            </h3>
          </Link>

          {/* Rating */}
          {product.average_rating && (
            <div className="flex items-center gap-1 mb-2">
              <div className="flex">{renderStars(product.average_rating)}</div>
              <span className="text-xs text-gray-600">
                ({product.review_count || 0})
              </span>
            </div>
          )}

          {/* Price */}
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-bold text-green-600">
                {formatCurrency(discountedPrice)}
              </span>
              {hasDiscount && (
                <span className="text-sm text-gray-500 line-through">
                  {formatCurrency(product.price_xaf)}
                </span>
              )}
            </div>
            
            {hasDiscount && (
              <p className="text-xs text-green-600">
                Save {formatCurrency(product.price_xaf - discountedPrice)}
              </p>
            )}
          </div>
        </CardContent>

        <CardFooter className="p-4 pt-0">
          <Button
            className="w-full"
            onClick={() => onAddToCart(product.id)}
            disabled={!isInStock}
          >
            <ShoppingCart className="h-4 w-4 mr-2" />
            {isInStock ? 'Add to Cart' : 'Out of Stock'}
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  );
};
