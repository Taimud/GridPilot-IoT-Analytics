const CACHE_NAME = "gridpilot-v1";
const ASSETS_TO_CACHE = [
    "/",
    "index.html",
    "analytics.html",
    "notifications.html",
    "profile.html",
    "settings.html",
    "personal_info.html",
    "login.html",
    "manifest.json",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
    "https://cdn.jsdelivr.net/npm/chart.js"
];

// 1. Install Event (Save files to cache)
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log("Caching App Shell...");
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// 2. Fetch Event (Serve cached files if offline)
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            // Return cached version or fetch from network
            return response || fetch(event.request);
        })
    );
});