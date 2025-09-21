/**
 * Product API functions for PromoWeb Africa
 */

import { 
  Product, 
  ProductListParams, 
  ProductListResponse, 
  ProductSearchParams,
  ProductSearchResponse,
  FilterOptions,
  ProductReviewCreateRequest,
  ProductCreateRequest,
  ProductUpdateRequest
} from '@/types/product';
import { apiClient } from './client';

export const productApi = {
  /**
   * Get paginated list of products
   */
  async getProducts(params: ProductListParams = {}): Promise<ProductListResponse> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v.toString()));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    const response = await apiClient.get(`/api/v1/products?${searchParams}`);
    return response.data;
  },

  /**
   * Search products with full-text search
   */
  async searchProducts(params: ProductSearchParams): Promise<ProductSearchResponse> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });

    const response = await apiClient.get(`/api/v1/products/search?${searchParams}`);
    return response.data;
  },

  /**
   * Get single product by ID
   */
  async getProduct(productId: string): Promise<Product> {
    const response = await apiClient.get(`/api/v1/products/${productId}`);
    return response.data;
  },

  /**
   * Get product by slug
   */
  async getProductBySlug(slug: string): Promise<Product> {
    const response = await apiClient.get(`/api/v1/products/slug/${slug}`);
    return response.data;
  },

  /**
   * Get filter options for product listing
   */
  async getFilterOptions(categoryId?: string): Promise<FilterOptions> {
    const params = categoryId ? `?category_id=${categoryId}` : '';
    const response = await apiClient.get(`/api/v1/products/filters${params}`);
    return response.data;
  },

  /**
   * Get related products
   */
  async getRelatedProducts(productId: string, limit: number = 6): Promise<Product[]> {
    const response = await apiClient.get(`/api/v1/products/${productId}/related?limit=${limit}`);
    return response.data;
  },

  /**
   * Create product review
   */
  async createReview(productId: string, review: ProductReviewCreateRequest): Promise<any> {
    const response = await apiClient.post(`/api/v1/products/${productId}/reviews`, review);
    return response.data;
  },

  /**
   * Get product reviews
   */
  async getReviews(productId: string, page: number = 1, perPage: number = 10): Promise<any> {
    const response = await apiClient.get(
      `/api/v1/products/${productId}/reviews?page=${page}&per_page=${perPage}`
    );
    return response.data;
  },

  /**
   * Admin: Create product
   */
  async createProduct(product: ProductCreateRequest): Promise<Product> {
    const response = await apiClient.post('/api/v1/products', product);
    return response.data;
  },

  /**
   * Admin: Update product
   */
  async updateProduct(productId: string, updates: ProductUpdateRequest): Promise<Product> {
    const response = await apiClient.put(`/api/v1/products/${productId}`, updates);
    return response.data;
  },

  /**
   * Admin: Delete product
   */
  async deleteProduct(productId: string): Promise<void> {
    await apiClient.delete(`/api/v1/products/${productId}`);
  },

  /**
   * Get featured products
   */
  async getFeaturedProducts(limit: number = 12): Promise<Product[]> {
    const response = await apiClient.get(`/api/v1/products?is_featured=true&per_page=${limit}`);
    return response.data.items;
  },

  /**
   * Get new arrivals
   */
  async getNewArrivals(limit: number = 12): Promise<Product[]> {
    const response = await apiClient.get(`/api/v1/products?sort_by=created_at&per_page=${limit}`);
    return response.data.items;
  },

  /**
   * Get products on sale
   */
  async getProductsOnSale(limit: number = 12): Promise<Product[]> {
    const response = await apiClient.get(`/api/v1/products?has_discount=true&per_page=${limit}`);
    return response.data.items;
  },

  /**
   * Get popular products
   */
  async getPopularProducts(limit: number = 12): Promise<Product[]> {
    const response = await apiClient.get(`/api/v1/products?sort_by=popularity&per_page=${limit}`);
    return response.data.items;
  }
};
