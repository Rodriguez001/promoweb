/**
 * Cart type definitions for PromoWeb Africa
 */

import { Product } from './product';

export interface CartItem {
  id: string;
  cart_id: string;
  product_id: string;
  product?: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
  notes?: string;
  
  // Calculated fields
  current_price: number;
  savings: number;
  is_available: boolean;
  availability_message?: string;
  max_available_quantity: number;
  
  // Product info for display
  product_title: string;
  product_image?: string;
  product_brand?: string;
  product_weight_kg?: number;
  
  created_at: string;
  updated_at: string;
}

export interface CartTotals {
  subtotal: number;
  tax_amount: number;
  shipping_estimate: number;
  discount_amount: number;
  total: number;
  item_count: number;
  savings_total: number;
}

export interface Cart {
  id: string;
  user_id?: string;
  session_id?: string;
  items: CartItem[];
  totals: CartTotals;
  expires_at?: string;
  is_expired: boolean;
  is_empty: boolean;
  created_at: string;
  updated_at: string;
}

export interface SavedItem {
  id: string;
  user_id: string;
  product_id: string;
  product?: Product;
  list_name: string;
  notes?: string;
  notify_on_price_drop: boolean;
  price_when_saved: number;
  
  // Calculated fields
  current_price: number;
  price_difference: number;
  price_dropped: boolean;
  savings_amount: number;
  
  // Product info
  product_title: string;
  product_image?: string;
  product_brand?: string;
  product_is_available: boolean;
  
  created_at: string;
  updated_at: string;
}

// API Request types
export interface AddToCartRequest {
  product_id: string;
  quantity: number;
  notes?: string;
}

export interface UpdateCartItemRequest {
  quantity: number;
  notes?: string;
}

export interface ClearCartRequest {
  confirm: boolean;
}

export interface SavedItemCreateRequest {
  product_id: string;
  list_name: string;
  notes?: string;
  notify_on_price_drop?: boolean;
}

export interface MoveToCartRequest {
  saved_item_id: string;
  quantity?: number;
}

// API Response types
export interface CartResponse extends Cart {}

export interface CartDetail extends Cart {}

export interface SavedItemsList {
  lists: Record<string, SavedItem[]>;
  total_items: number;
  price_drop_alerts: number;
}

export interface CartValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  unavailable_items: string[];
  quantity_adjustments: Record<string, number>;
}

export interface CartSummary {
  cart_id: string;
  total_items: number;
  subtotal: number;
  estimated_tax: number;
  estimated_shipping: number;
  estimated_total: number;
  items_summary: Array<{
    product_id: string;
    title: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    image?: string;
  }>;
  requires_shipping: boolean;
  estimated_weight: number;
}

export interface PromoCodeResult {
  valid: boolean;
  code: string;
  discount_amount: number;
  discount_type: 'percentage' | 'fixed_amount';
  message: string;
}
