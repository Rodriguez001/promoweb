/**
 * Product type definitions for PromoWeb Africa
 */

export interface Product {
  id: string;
  title: string;
  description: string;
  brand?: string;
  sku: string;
  slug: string;
  
  // Pricing
  price_eur: number;
  price_xaf: number;
  discount_percentage?: number;
  margin_percentage: number;
  
  // Images
  main_image?: string;
  additional_images: string[];
  
  // Categorization
  category_id: string;
  category?: Category;
  tags: string[];
  
  // Physical properties
  weight_kg?: number;
  dimensions?: {
    length: number;
    width: number;
    height: number;
  };
  
  // Status
  is_active: boolean;
  is_featured: boolean;
  is_digital: boolean;
  
  // Inventory
  inventory?: Inventory;
  
  // Reviews & ratings
  average_rating?: number;
  review_count?: number;
  reviews?: ProductReview[];
  
  // SEO
  meta_title?: string;
  meta_description?: string;
  
  // Timestamps
  created_at: string;
  updated_at: string;
  
  // Related products
  related_products?: Product[];
  
  // Promotions
  promotions?: Promotion[];
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  parent_id?: string;
  image_url?: string;
  sort_order: number;
  is_active: boolean;
  meta_title?: string;
  meta_description?: string;
  created_at: string;
  updated_at: string;
}

export interface Inventory {
  id: string;
  product_id: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  min_threshold: number;
  max_threshold?: number;
  location?: string;
  last_updated: string;
}

export interface ProductReview {
  id: string;
  product_id: string;
  user_id: string;
  user_name: string;
  rating: number;
  title?: string;
  comment?: string;
  is_approved: boolean;
  is_verified_purchase: boolean;
  created_at: string;
  updated_at: string;
}

export interface Promotion {
  id: string;
  name: string;
  description?: string;
  discount_type: 'percentage' | 'fixed_amount';
  discount_value: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
  min_order_amount?: number;
  max_discount_amount?: number;
  usage_limit?: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

// API Request/Response types
export interface ProductListParams {
  page?: number;
  per_page?: number;
  category_id?: string;
  search?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  in_stock?: boolean;
  is_featured?: boolean;
  sort_by?: 'created_at' | 'price_asc' | 'price_desc' | 'name' | 'popularity';
  brands?: string[];
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ProductSearchParams {
  q: string;
  page?: number;
  per_page?: number;
  category_id?: string;
  min_price?: number;
  max_price?: number;
  sort_by?: 'relevance' | 'price_asc' | 'price_desc' | 'name' | 'created_at';
}

export interface ProductSearchResponse {
  products: ProductListResponse;
  facets: {
    categories: Array<{
      id: string;
      name: string;
      count: number;
    }>;
    brands: Array<{
      name: string;
      count: number;
    }>;
  };
  suggestions: string[];
  total_results: number;
  search_time_ms: number;
}

export interface FilterOptions {
  categories: Array<{
    id: string;
    name: string;
    count: number;
  }>;
  brands: Array<{
    name: string;
    count: number;
  }>;
  price_range: {
    min: number;
    max: number;
  };
}

export interface ProductCreateRequest {
  title: string;
  description: string;
  brand?: string;
  sku: string;
  price_eur: number;
  margin_percentage: number;
  category_id: string;
  tags: string[];
  weight_kg?: number;
  dimensions?: {
    length: number;
    width: number;
    height: number;
  };
  is_featured?: boolean;
  is_digital?: boolean;
  meta_title?: string;
  meta_description?: string;
}

export interface ProductUpdateRequest extends Partial<ProductCreateRequest> {
  is_active?: boolean;
}

export interface ProductReviewCreateRequest {
  product_id: string;
  rating: number;
  title?: string;
  comment?: string;
}
