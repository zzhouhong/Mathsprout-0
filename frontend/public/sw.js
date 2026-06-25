/**
 * Minimal service worker — caches the app shell for offline access.
 * Works alongside Next.js built-in asset caching.
 */

const CACHE_NAME = "kindergarten-math-v1";
const SHELL_URLS = ["/", "/login", "/parent"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Only handle navigation (page) requests — let Next.js handle assets
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(() =>
        caches.match(event.request).then(
          (cached) =>
            cached ||
            caches.match("/").then(
              (fallback) => fallback || new Response("离线模式 — 请连接网络后重试", {
                status: 503,
                headers: { "Content-Type": "text/plain; charset=utf-8" },
              })
            )
        )
      )
    );
  }
});
