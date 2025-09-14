self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open("tronexi-cache").then((cache) => {
      return cache.addAll([
        "/", 
        "/static/icons/icon-192x192.png",
        "/static/icons/icon-512x512.png",
        // add more static files if you want offline caching
      ]);
    })
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
