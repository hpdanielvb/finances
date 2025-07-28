// OrçaZenFinanceiro Service Worker
// PWA Implementation with offline support and background sync

const CACHE_NAME = 'orcazen-v1.0.0';
const STATIC_CACHE = 'orcazen-static-v1';
const DYNAMIC_CACHE = 'orcazen-dynamic-v1';
const API_CACHE = 'orcazen-api-v1';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// API endpoints to cache
const API_ENDPOINTS = [
  '/api/dashboard',
  '/api/transactions',
  '/api/accounts',
  '/api/categories',
  '/api/budgets',
  '/api/contratos',
  '/api/credit-cards/invoices'
];

// IndexedDB setup for offline data
const DB_NAME = 'OrcaZenDB';
const DB_VERSION = 1;
const STORES = {
  transactions: 'transactions',
  accounts: 'accounts',
  categories: 'categories',
  sync_queue: 'sync_queue'
};

// Install Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static assets
      caches.open(STATIC_CACHE).then((cache) => {
        console.log('[SW] Pre-caching static assets');
        return cache.addAll(STATIC_ASSETS);
      }),
      
      // Initialize IndexedDB
      initializeIndexedDB(),
      
      // Skip waiting to activate immediately
      self.skipWaiting()
    ])
  );
});

// Activate Service Worker
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && 
                cacheName !== DYNAMIC_CACHE && 
                cacheName !== API_CACHE) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Claim all clients
      self.clients.claim()
    ])
  );
});

// Fetch Event - Network strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-HTTP requests
  if (!request.url.startsWith('http')) {
    return;
  }
  
  // API requests - Cache First with Network Fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }
  
  // Static assets - Cache First
  if (STATIC_ASSETS.some(asset => request.url.includes(asset))) {
    event.respondWith(handleStaticRequest(request));
    return;
  }
  
  // HTML pages - Network First with Cache Fallback
  if (request.destination === 'document') {
    event.respondWith(handleDocumentRequest(request));
    return;
  }
  
  // Other resources - Stale While Revalidate
  event.respondWith(handleOtherRequest(request));
});

// API Request Handler
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try network first
    const networkResponse = await fetch(request.clone());
    
    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
      
      // Store in IndexedDB for offline access
      if (request.method === 'GET') {
        const data = await networkResponse.clone().json();
        await storeInIndexedDB(url.pathname, data);
      }
      
      return networkResponse;
    }
    
    throw new Error('Network response not ok');
    
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', url.pathname);
    
    // Try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Try IndexedDB for GET requests
    if (request.method === 'GET') {
      const offlineData = await getFromIndexedDB(url.pathname);
      if (offlineData) {
        return new Response(JSON.stringify(offlineData), {
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }
    
    // For POST/PUT/DELETE requests when offline, queue for sync
    if (['POST', 'PUT', 'DELETE'].includes(request.method)) {
      await queueForSync(request);
      return new Response(JSON.stringify({ 
        message: 'Operação salva para sincronização quando voltar online',
        offline: true 
      }), {
        status: 202,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Return offline fallback
    return new Response(JSON.stringify({ 
      error: 'Offline - dados não disponíveis',
      offline: true 
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Static Request Handler
async function handleStaticRequest(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    return new Response('Recurso não disponível offline', { status: 503 });
  }
}

// Document Request Handler
async function handleDocumentRequest(request) {
  try {
    const networkResponse = await fetch(request);
    const cache = await caches.open(DYNAMIC_CACHE);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    return cachedResponse || await caches.match('/');
  }
}

// Other Request Handler
async function handleOtherRequest(request) {
  const cachedResponse = await caches.match(request);
  
  const networkFetch = fetch(request).then((response) => {
    if (response.ok) {
      const cache = caches.open(DYNAMIC_CACHE);
      cache.then(c => c.put(request, response.clone()));
    }
    return response;
  }).catch(() => cachedResponse);
  
  return cachedResponse || networkFetch;
}

// Background Sync
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-transactions') {
    event.waitUntil(syncQueuedRequests());
  }
});

// IndexedDB Functions
async function initializeIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Create object stores
      Object.values(STORES).forEach(storeName => {
        if (!db.objectStoreNames.contains(storeName)) {
          const store = db.createObjectStore(storeName, { keyPath: 'id', autoIncrement: true });
          
          if (storeName === 'sync_queue') {
            store.createIndex('timestamp', 'timestamp');
          }
        }
      });
    };
  });
}

async function storeInIndexedDB(endpoint, data) {
  try {
    const db = await initializeIndexedDB();
    const transaction = db.transaction(['transactions'], 'readwrite');
    const store = transaction.objectStore('transactions');
    
    await store.put({
      id: endpoint,
      data: data,
      timestamp: Date.now()
    });
  } catch (error) {
    console.error('[SW] Error storing in IndexedDB:', error);
  }
}

async function getFromIndexedDB(endpoint) {
  try {
    const db = await initializeIndexedDB();
    const transaction = db.transaction(['transactions'], 'readonly');
    const store = transaction.objectStore('transactions');
    const result = await store.get(endpoint);
    
    return result ? result.data : null;
  } catch (error) {
    console.error('[SW] Error getting from IndexedDB:', error);
    return null;
  }
}

async function queueForSync(request) {
  try {
    const db = await initializeIndexedDB();
    const transaction = db.transaction(['sync_queue'], 'readwrite');
    const store = transaction.objectStore('sync_queue');
    
    const requestData = {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body: request.method !== 'GET' ? await request.text() : null,
      timestamp: Date.now()
    };
    
    await store.add(requestData);
    
    // Register for background sync
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-transactions');
    }
    
    console.log('[SW] Request queued for sync:', request.url);
  } catch (error) {
    console.error('[SW] Error queuing for sync:', error);
  }
}

async function syncQueuedRequests() {
  try {
    const db = await initializeIndexedDB();
    const transaction = db.transaction(['sync_queue'], 'readwrite');
    const store = transaction.objectStore('sync_queue');
    const requests = await store.getAll();
    
    for (const requestData of requests) {
      try {
        const response = await fetch(requestData.url, {
          method: requestData.method,
          headers: requestData.headers,
          body: requestData.body
        });
        
        if (response.ok) {
          await store.delete(requestData.id);
          console.log('[SW] Synced request:', requestData.url);
        }
      } catch (error) {
        console.error('[SW] Failed to sync request:', requestData.url, error);
      }
    }
  } catch (error) {
    console.error('[SW] Error during sync:', error);
  }
}

// Push notifications (future enhancement)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    
    const options = {
      body: data.body || 'Nova notificação do OrçaZen',
      icon: '/icon-192x192.png',
      badge: '/icon-192x192.png',
      vibrate: [200, 100, 200],
      tag: 'orcazen-notification',
      actions: [
        {
          action: 'view',
          title: 'Visualizar',
          icon: '/icon-192x192.png'
        },
        {
          action: 'dismiss',
          title: 'Dispensar'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'OrçaZen', options)
    );
  }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('[SW] Service Worker loaded successfully');