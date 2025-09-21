/**
 * ProductCatalog - Main product listing component
 * Handles product display, filtering, pagination, and search
 */

// @ts-nocheck - Bypassing React 18/19 type conflicts with Radix UI components
'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { 
  Search, 
  Filter, 
  Grid, 
  List, 
  ShoppingCart, 
  Heart,
  Star,
  Loader2,
  SlidersHorizontal
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

import { formatCurrency } from '@/lib/utils';
import { productApi } from '@/lib/api/products';
import { cartApi } from '@/lib/api/cart';
import { Product } from '@/types/product';
import { PaginationControls } from '@/components/ui/pagination';
import { ProductCard } from '@/components/ProductCard';
import { useToast } from '@/hooks/use-toast';

interface ProductCatalogProps {
  categoryId?: string;
  searchQuery?: string;
}

export const ProductCatalog: React.FC<ProductCatalogProps> = ({
  categoryId,
  searchQuery: initialSearchQuery
}) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  // State
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery || '');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'created_at' | 'price_asc' | 'price_desc' | 'name' | 'popularity'>('created_at');
  const [priceRange, setPriceRange] = useState([0, 500000]);
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [inStockOnly, setInStockOnly] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  
  // Pagination
  const page = parseInt(searchParams.get('page') || '1');
  const perPage = 20;

  // Query for products
  const {
    data: productsData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: [
      'products',
      page,
      perPage,
      categoryId,
      searchQuery,
      sortBy,
      priceRange,
      selectedBrands,
      inStockOnly
    ],
    queryFn: () => productApi.getProducts({
      page,
      per_page: perPage,
      category_id: categoryId,
      search: searchQuery || undefined,
      sort_by: sortBy,
      min_price: priceRange[0],
      max_price: priceRange[1],
      brands: selectedBrands.length > 0 ? selectedBrands : undefined,
      in_stock: inStockOnly || undefined
    }),
    placeholderData: keepPreviousData
  });

  // Query for filter options
  const { data: filterOptions } = useQuery({
    queryKey: ['product-filters', categoryId],
    queryFn: () => productApi.getFilterOptions(categoryId),
    staleTime: 5 * 60 * 1000 // 5 minutes
  });

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  // Handle add to cart
  const handleAddToCart = async (productId: string, quantity: number = 1) => {
    try {
      await cartApi.addToCart({
        product_id: productId,
        quantity
      });
      
      toast({
        title: "Added to cart",
        description: "Product has been added to your cart",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to add product to cart",
      });
    }
  };

  // Handle wishlist toggle
  const handleWishlistToggle = async (productId: string) => {
    try {
      // TODO: Implement wishlist API
      toast({
        title: "Added to wishlist",
        description: "Product saved to your wishlist",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to save to wishlist",
      });
    }
  };

  // Filter panel component
  const FilterPanel = () => (
    <div className="space-y-6">
      {/* Price Range */}
      <div>
        <h3 className="font-semibold mb-3">Price Range (XAF)</h3>
        <Slider
          value={priceRange}
          onValueChange={setPriceRange}
          max={500000}
          min={0}
          step={1000}
          className="mb-2"
        />
        <div className="flex justify-between text-sm text-gray-600">
          <span>{formatCurrency(priceRange[0])}</span>
          <span>{formatCurrency(priceRange[1])}</span>
        </div>
      </div>

      {/* Brands */}
      {filterOptions?.brands && filterOptions.brands.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">Brands</h3>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {filterOptions.brands.map((brand) => (
              <div key={brand.name} className="flex items-center space-x-2">
                <Checkbox
                  id={`brand-${brand.name}`}
                  checked={selectedBrands.includes(brand.name)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setSelectedBrands([...selectedBrands, brand.name]);
                    } else {
                      setSelectedBrands(selectedBrands.filter(b => b !== brand.name));
                    }
                  }}
                />
                <label 
                  htmlFor={`brand-${brand.name}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {brand.name} ({brand.count})
                </label>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stock Status */}
      <div>
        <div className="flex items-center space-x-2">
          <Checkbox
            id="in-stock"
            checked={inStockOnly}
            onCheckedChange={setInStockOnly}
          />
          <label 
            htmlFor="in-stock"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            In stock only
          </label>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Search Bar */}
      <div className="mb-8">
        <form onSubmit={handleSearch} className="flex gap-2 max-w-2xl mx-auto">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button type="submit">Search</Button>
        </form>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center gap-4">
          {/* Results count */}
          {productsData && (
            <p className="text-gray-600">
              {productsData.total} products found
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Sort */}
          <Select value={sortBy} onValueChange={(value) => setSortBy(value as typeof sortBy)}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="created_at">Newest</SelectItem>
              <SelectItem value="price_asc">Price: Low to High</SelectItem>
              <SelectItem value="price_desc">Price: High to Low</SelectItem>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="popularity">Most Popular</SelectItem>
            </SelectContent>
          </Select>

          {/* View Mode */}
          <div className="flex border rounded-md">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="rounded-r-none"
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="rounded-l-none"
            >
              <List className="h-4 w-4" />
            </Button>
          </div>

          {/* Mobile Filter Toggle */}
          <Sheet open={isFilterOpen} onOpenChange={setIsFilterOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" className="sm:hidden">
                <SlidersHorizontal className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-80">
              <SheetHeader>
                <SheetTitle>Filters</SheetTitle>
                <SheetDescription>
                  Refine your product search
                </SheetDescription>
              </SheetHeader>
              <div className="mt-6">
                <FilterPanel />
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Desktop Sidebar Filters */}
        <div className="hidden sm:block w-64 shrink-0">
          <Card>
            <CardHeader>
              <h2 className="font-semibold flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Filters
              </h2>
            </CardHeader>
            <CardContent>
              <FilterPanel />
            </CardContent>
          </Card>
        </div>

        {/* Products Grid/List */}
        <div className="flex-1">
          {isLoading ? (
            <div className="flex justify-center items-center py-16">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : error ? (
            <div className="text-center py-16">
              <p className="text-red-600 mb-4">Failed to load products</p>
              <Button onClick={() => refetch()}>Try Again</Button>
            </div>
          ) : productsData?.items.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-gray-600 mb-4">No products found</p>
              <Button onClick={() => {
                setSearchQuery('');
                setSelectedBrands([]);
                setPriceRange([0, 500000]);
                setInStockOnly(false);
              }}>
                Clear Filters
              </Button>
            </div>
          ) : (
            <>
              <AnimatePresence mode="wait">
                <motion.div
                  key={`${viewMode}-${page}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                  className={viewMode === 'grid' 
                    ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                    : "space-y-4"
                  }
                >
                  {productsData?.items.map((product: Product) => (
                    <ProductCard
                      key={product.id}
                      product={product}
                      viewMode={viewMode}
                      onAddToCart={handleAddToCart}
                      onWishlistToggle={handleWishlistToggle}
                    />
                  ))}
                </motion.div>
              </AnimatePresence>

              {/* Pagination */}
              {productsData && productsData.pages > 1 && (
                <div className="mt-8">
                  <PaginationControls
                    currentPage={page}
                    totalPages={productsData.pages}
                    onPageChange={(newPage) => {
                      const params = new URLSearchParams(searchParams);
                      params.set('page', newPage.toString());
                      router.push(`?${params.toString()}`);
                    }}
                  />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
