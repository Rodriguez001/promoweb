/**
 * Cart API functions for PromoWeb Africa
 */

import {
  Cart,
  CartDetail,
  CartItem,
  AddToCartRequest,
  UpdateCartItemRequest,
  ClearCartRequest,
  SavedItem,
  SavedItemCreateRequest,
  SavedItemsList,
  MoveToCartRequest,
  CartValidationResult,
  CartSummary,
  PromoCodeResult
} from '@/types/cart';
import { apiClient } from './client';

export const cartApi = {
  /**
   * Get current user's cart
   */
  async getCart(): Promise<CartDetail> {
    const response = await apiClient.get('/api/v1/cart');
    return response.data;
  },

  /**
   * Add item to cart
   */
  async addToCart(item: AddToCartRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/cart/items', item);
    return response.data;
  },

  /**
   * Update cart item
   */
  async updateCartItem(itemId: string, updates: UpdateCartItemRequest): Promise<{ message: string }> {
    const response = await apiClient.put(`/api/v1/cart/items/${itemId}`, updates);
    return response.data;
  },

  /**
   * Remove item from cart
   */
  async removeCartItem(itemId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/api/v1/cart/items/${itemId}`);
    return response.data;
  },

  /**
   * Clear entire cart
   */
  async clearCart(): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/cart/clear', { confirm: true });
    return response.data;
  },

  /**
   * Validate cart items
   */
  async validateCart(): Promise<CartValidationResult> {
    const response = await apiClient.get('/api/v1/cart/validate');
    return response.data;
  },

  /**
   * Get cart summary for checkout
   */
  async getCartSummary(): Promise<CartSummary> {
    const response = await apiClient.get('/api/v1/cart/summary');
    return response.data;
  },

  /**
   * Apply promo code
   */
  async applyPromoCode(code: string): Promise<PromoCodeResult> {
    const response = await apiClient.post('/api/v1/cart/promo-code', { code });
    return response.data;
  },

  /**
   * Remove promo code
   */
  async removePromoCode(): Promise<{ message: string }> {
    const response = await apiClient.delete('/api/v1/cart/promo-code');
    return response.data;
  },

  // Wishlist/Saved Items
  /**
   * Get saved items (wishlist)
   */
  async getSavedItems(): Promise<SavedItemsList> {
    const response = await apiClient.get('/api/v1/cart/saved');
    return response.data;
  },

  /**
   * Save item to wishlist
   */
  async saveItem(item: SavedItemCreateRequest): Promise<SavedItem> {
    const response = await apiClient.post('/api/v1/cart/saved', item);
    return response.data;
  },

  /**
   * Remove saved item
   */
  async removeSavedItem(itemId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/api/v1/cart/saved/${itemId}`);
    return response.data;
  },

  /**
   * Move saved item to cart
   */
  async moveToCart(request: MoveToCartRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/api/v1/cart/saved/move-to-cart', request);
    return response.data;
  },

  /**
   * Update saved item
   */
  async updateSavedItem(itemId: string, updates: Partial<SavedItemCreateRequest>): Promise<SavedItem> {
    const response = await apiClient.put(`/api/v1/cart/saved/${itemId}`, updates);
    return response.data;
  },

  // Bulk operations
  /**
   * Add multiple items to cart
   */
  async addMultipleToCart(items: AddToCartRequest[]): Promise<{ message: string; failed_items?: string[] }> {
    const response = await apiClient.post('/api/v1/cart/items/bulk', { items });
    return response.data;
  },

  /**
   * Update multiple cart items
   */
  async updateMultipleItems(updates: Array<{ item_id: string } & UpdateCartItemRequest>): Promise<{ message: string }> {
    const response = await apiClient.put('/api/v1/cart/items/bulk', { updates });
    return response.data;
  },

  /**
   * Remove multiple cart items
   */
  async removeMultipleItems(itemIds: string[]): Promise<{ message: string }> {
    const response = await apiClient.delete('/api/v1/cart/items/bulk', { 
      data: { item_ids: itemIds } 
    });
    return response.data;
  }
};
