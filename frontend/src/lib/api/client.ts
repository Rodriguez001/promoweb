/**
 * API client configuration for PromoWeb Africa
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

// Types
interface ApiError {
  message: string;
  details?: any;
  status?: number;
}

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth tokens
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Add session ID for anonymous users
      const sessionId = localStorage.getItem('session_id');
      if (sessionId) {
        config.headers['X-Session-ID'] = sessionId;
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    const apiError: ApiError = {
      message: 'An unexpected error occurred',
      status: error.response?.status,
    };

    if (error.response?.data) {
      const errorData = error.response.data as any;
      apiError.message = errorData.detail || errorData.message || apiError.message;
      apiError.details = errorData;
    } else if (error.request) {
      apiError.message = 'Network error - please check your connection';
    } else {
      apiError.message = error.message || apiError.message;
    }

    // Handle specific status codes
    switch (error.response?.status) {
      case 401:
        // Unauthorized - clear auth token and redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          window.location.href = '/auth/login';
        }
        break;
      case 403:
        apiError.message = 'Access denied';
        break;
      case 404:
        apiError.message = 'Resource not found';
        break;
      case 422:
        apiError.message = 'Invalid data provided';
        break;
      case 429:
        apiError.message = 'Too many requests - please try again later';
        break;
      case 500:
        apiError.message = 'Server error - please try again later';
        break;
    }

    return Promise.reject(apiError);
  }
);

// Helper functions
export const setAuthToken = (token: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('auth_token', token);
  }
};

export const removeAuthToken = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token');
  }
};

export const setSessionId = (sessionId: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('session_id', sessionId);
  }
};

export const getSessionId = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('session_id');
  }
  return null;
};

// Generate session ID for anonymous users
export const generateSessionId = (): string => {
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  setSessionId(sessionId);
  return sessionId;
};

// API response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.message) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unexpected error occurred';
};

export default apiClient;
