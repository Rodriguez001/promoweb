/**
 * Service Worker for PromoWeb Africa PWA
 * Handles caching, offline functionality, and background sync
 */

const CACHE_NAME = 'promoweb-v1.0.0';
const STATIC_CACHE_NAME = 'promoweb-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'promoweb-dynamic-v1.0.0';

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/offline.html',
  '/_next/static/css/app.css',
  '/_next/static/chunks/pages/_app.js',
  '/_next/static/chunks/pages/_document.js',
  '/_next/static/chunks/pages/index.js'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /\/api\/v1\/products/,
  /\/api\/v1\/categories/,
  /\/api\/v1\/cart/
];

// Background sync patterns
const SYNC_PATTERNS = [
  'cart-sync',
  'order-sync',
  'analytics-sync'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static assets', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME && 
                cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - handle network requests with caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and chrome-extension requests
  if (request.method !== 'GET' || url.protocol.startsWith('chrome-extension')) {
    return;
  }

  // Handle different types of requests
  if (url.pathname.startsWith('/api/')) {
    // API requests - Network First with cache fallback
    event.respondWith(handleApiRequest(request));
  } else if (url.pathname.startsWith('/_next/static/')) {
    // Static assets - Cache First
    event.respondWith(handleStaticAssets(request));
  } else if (url.pathname.match(/\.(png|jpg|jpeg|svg|gif|webp|ico)$/)) {
    // Images - Cache First with network fallback
    event.respondWith(handleImageRequest(request));
  } else {
    // HTML pages - Network First with cache fallback
    event.respondWith(handlePageRequest(request));
  }
});

// Background sync event
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync triggered:', event.tag);
  
  if (event.tag === 'cart-sync') {
    event.waitUntil(syncCartData());
  } else if (event.tag === 'order-sync') {
    event.waitUntil(syncOrderData());
  } else if (event.tag === 'analytics-sync') {
    event.waitUntil(syncAnalyticsData());
  }
});

// Push event for notifications
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push received');
  
  let data = {};
  if (event.data) {
    data = event.data.json();
  }

  const options = {
    body: data.body || 'Nouvelle notification PromoWeb Africa',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    data: data.data || {},
    actions: [
      {
        action: 'view',
        title: 'Voir',
        icon: '/icons/view-icon.png'
      },
      {
        action: 'dismiss',
        title: 'Ignorer',
        icon: '/icons/dismiss-icon.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'PromoWeb Africa', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked');
  
  event.notification.close();

  if (event.action === 'view') {
    const urlToOpen = event.notification.data.url || '/';
    
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          // Check if a window is already open
          for (const client of clientList) {
            if (client.url === urlToOpen && 'focus' in client) {
              return client.focus();
            }
          }
          // Open new window
          if (clients.openWindow) {
            return clients.openWindow(urlToOpen);
          }
        })
    );
  }
});

// Handle API requests - Network First strategy
async function handleApiRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful responses for API calls that should be cached
      const shouldCache = API_CACHE_PATTERNS.some(pattern => 
        pattern.test(request.url)
      );
      
      if (shouldCache) {
        const cache = await caches.open(DYNAMIC_CACHE_NAME);
        cache.put(request, networkResponse.clone());
      }
      
      return networkResponse;
    }
  } catch (error) {
    console.log('Service Worker: Network failed for API request', error);
  }

  // Fallback to cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // Return offline response for failed API calls
  return new Response(
    JSON.stringify({ 
      error: 'Offline', 
      message: 'Cette fonctionnalité nécessite une connexion internet' 
    }),
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

// Handle static assets - Cache First strategy
async function handleStaticAssets(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('Service Worker: Failed to fetch static asset', error);
  }

  // Return empty response for failed static assets
  return new Response('', { status: 404 });
}

// Handle image requests - Cache First strategy
async function handleImageRequest(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('Service Worker: Failed to fetch image', error);
  }

  // Return placeholder image for failed images
  return caches.match('/images/placeholder.png') || 
         new Response('', { status: 404 });
}

// Handle page requests - Network First with cache fallback
async function handlePageRequest(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('Service Worker: Network failed for page request', error);
  }

  // Fallback to cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // Return offline page
  return caches.match('/offline.html') || 
         new Response('Offline', { status: 503 });
}

// Background sync functions
async function syncCartData() {
  try {
    console.log('Service Worker: Syncing cart data');
    
    // Get stored cart operations from IndexedDB
    const cartOperations = await getStoredCartOperations();
    
    for (const operation of cartOperations) {
      try {
        await fetch('/api/v1/cart/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(operation)
        });
        
        // Remove synced operation from storage
        await removeCartOperation(operation.id);
      } catch (error) {
        console.error('Service Worker: Failed to sync cart operation', error);
      }
    }
  } catch (error) {
    console.error('Service Worker: Cart sync failed', error);
  }
}

async function syncOrderData() {
  try {
    console.log('Service Worker: Syncing order data');
    // Implementation for order sync
  } catch (error) {
    console.error('Service Worker: Order sync failed', error);
  }
}

async function syncAnalyticsData() {
  try {
    console.log('Service Worker: Syncing analytics data');
    
    // Get stored analytics events
    const events = await getStoredAnalyticsEvents();
    
    if (events.length > 0) {
      await fetch('/api/v1/analytics/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events })
      });
      
      // Clear synced events
      await clearAnalyticsEvents();
    }
  } catch (error) {
    console.error('Service Worker: Analytics sync failed', error);
  }
}

// IndexedDB helper functions (simplified)
async function getStoredCartOperations() {
  // Implementation would use IndexedDB to get stored operations
  return [];
}

async function removeCartOperation(id) {
  // Implementation would remove operation from IndexedDB
}

async function getStoredAnalyticsEvents() {
  // Implementation would get analytics events from IndexedDB
  return [];
}

async function clearAnalyticsEvents() {
  // Implementation would clear analytics events from IndexedDB
}

// Cache management
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(DYNAMIC_CACHE_NAME)
        .then(cache => cache.addAll(event.data.payload))
    );
  }
});
