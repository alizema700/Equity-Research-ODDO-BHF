// ODDO BHF Sales Intelligence - Service Worker
const CACHE_NAME = 'oddo-sales-v1';
const STATIC_CACHE = 'oddo-static-v1';
const DYNAMIC_CACHE = 'oddo-dynamic-v1';

// Files to cache for offline support
const STATIC_FILES = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/Oddo_BHF_logo.svg.png',
  '/static/icons/app-icon.svg',
  '/static/icons/icon-192x192.svg',
  '/static/icons/icon-512x512.svg'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Pre-caching static assets');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => self.skipWaiting())
      .catch((err) => console.log('[SW] Cache error:', err))
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker...');
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== STATIC_CACHE && key !== DYNAMIC_CACHE) {
          console.log('[SW] Removing old cache:', key);
          return caches.delete(key);
        }
      }));
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip API calls (always fetch from network)
  if (event.request.url.includes('/api/') || event.request.url.includes('/search')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }

        return fetch(event.request)
          .then((fetchResponse) => {
            // Don't cache if not a valid response
            if (!fetchResponse || fetchResponse.status !== 200) {
              return fetchResponse;
            }

            // Clone the response
            const responseToCache = fetchResponse.clone();

            // Cache the fetched response
            caches.open(DYNAMIC_CACHE)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return fetchResponse;
          })
          .catch(() => {
            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
          });
      })
  );
});

// Push notification event
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  let notificationData = {
    title: 'ODDO BHF Alert',
    body: 'You have a new notification',
    icon: '/static/icons/app-icon.svg',
    badge: '/static/icons/icon-72x72.svg',
    tag: 'oddo-notification',
    data: { url: '/' }
  };

  // Parse push data if available
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = { ...notificationData, ...data };
    } catch (e) {
      notificationData.body = event.data.text();
    }
  }

  const options = {
    body: notificationData.body,
    icon: notificationData.icon,
    badge: notificationData.badge,
    tag: notificationData.tag,
    vibrate: [200, 100, 200],
    requireInteraction: notificationData.requireInteraction || false,
    actions: notificationData.actions || [
      { action: 'view', title: 'View' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    data: notificationData.data
  };

  event.waitUntil(
    self.registration.showNotification(notificationData.title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action);

  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  // Open the app or focus existing window
  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window open
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.postMessage({
              type: 'NOTIFICATION_CLICK',
              data: event.notification.data
            });
            return client.focus();
          }
        }
        // Open new window if none exists
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Background sync event (for offline actions)
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-alerts') {
    event.waitUntil(syncAlerts());
  }
});

// Sync alerts function
async function syncAlerts() {
  try {
    const response = await fetch('/api/alerts');
    const alerts = await response.json();

    // Check for new critical alerts
    for (const alert of alerts) {
      if (alert.priority === 'critical' && !alert.seen) {
        self.registration.showNotification('Critical Alert', {
          body: `${alert.ticker}: ${alert.message}`,
          icon: '/static/icons/app-icon.svg',
          badge: '/static/icons/icon-72x72.svg',
          tag: `alert-${alert.id}`,
          requireInteraction: true,
          data: { url: `/?alert=${alert.id}` }
        });
      }
    }
  } catch (error) {
    console.log('[SW] Sync failed:', error);
  }
}

// Periodic background sync (for scheduled notifications)
self.addEventListener('periodicsync', (event) => {
  console.log('[SW] Periodic sync:', event.tag);

  if (event.tag === 'check-earnings') {
    event.waitUntil(checkEarningsAlerts());
  }

  if (event.tag === 'check-prices') {
    event.waitUntil(checkPriceAlerts());
  }
});

// Check earnings alerts
async function checkEarningsAlerts() {
  // This would normally fetch from an API
  const earnings = [
    { ticker: 'MSFT', name: 'Microsoft', days: 2 },
    { ticker: 'AAPL', name: 'Apple', days: 4 }
  ];

  for (const earning of earnings) {
    if (earning.days <= 2) {
      self.registration.showNotification('Earnings Alert', {
        body: `${earning.ticker} (${earning.name}) reports earnings in ${earning.days} day${earning.days !== 1 ? 's' : ''}`,
        icon: '/static/icons/app-icon.svg',
        badge: '/static/icons/icon-72x72.svg',
        tag: `earnings-${earning.ticker}`,
        data: { url: '/?tab=dashboard', ticker: earning.ticker }
      });
    }
  }
}

// Check price alerts
async function checkPriceAlerts() {
  // This would normally fetch from an API
  const priceAlerts = [
    { ticker: 'NVDA', current: 950, target: 900, type: 'above' }
  ];

  for (const alert of priceAlerts) {
    if ((alert.type === 'above' && alert.current >= alert.target) ||
        (alert.type === 'below' && alert.current <= alert.target)) {
      self.registration.showNotification('Price Alert', {
        body: `${alert.ticker} has ${alert.type === 'above' ? 'risen above' : 'fallen below'} $${alert.target}! Current: $${alert.current}`,
        icon: '/static/icons/app-icon.svg',
        badge: '/static/icons/icon-72x72.svg',
        tag: `price-${alert.ticker}`,
        requireInteraction: true,
        data: { url: '/?stock=' + alert.ticker, ticker: alert.ticker }
      });
    }
  }
}

// Message event - for communication with main app
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);

  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data.type === 'TRIGGER_NOTIFICATION') {
    const { title, body, data } = event.data.payload;
    self.registration.showNotification(title, {
      body,
      icon: '/static/icons/app-icon.svg',
      badge: '/static/icons/icon-72x72.svg',
      tag: `manual-${Date.now()}`,
      data
    });
  }

  if (event.data.type === 'CACHE_URLS') {
    caches.open(DYNAMIC_CACHE).then((cache) => {
      cache.addAll(event.data.urls);
    });
  }
});

console.log('[SW] Service Worker loaded');
