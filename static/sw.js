const CACHE_NAME = 'prof-estagio-v1';
const ASSETS = [
  '/',
  '/static/index.html',
  '/static/assets/iel-logo.png',
  '/static/assets/professor.png',
  '/static/style.css',        // ajuste se tiver CSS separado
  '/static/manifest.json'
];

// Instala e faz cache dos arquivos essenciais
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Ativa e limpa caches antigos
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
});

// Intercepta requisições e serve do cache, ou cai no network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(cached => cached || fetch(event.request))
  );
});
