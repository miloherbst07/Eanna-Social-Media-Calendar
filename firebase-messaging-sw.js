/* Éanna Media Calendar: shows notifications on phones and laptops, even when the site is closed.
   Keep this file next to index.html on GitHub.
   It shows EVERY notification itself (app open or closed). iPhones switch off notifications
   for a site that receives a push without showing it, so nothing here is ever silent. */
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));

self.addEventListener("push", e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { d = { notification: { body: e.data ? e.data.text() : "" } }; }
  const n = d.notification || d.data || {};
  const link = (d.fcmOptions && d.fcmOptions.link) || n.click_action || self.registration.scope;
  e.waitUntil(self.registration.showNotification(n.title || "Éanna Media Calendar", {
    body: n.body || "",
    icon: n.icon || "icon-192.png",
    badge: "icon-192.png",
    data: { link }
  }));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  const link = (e.notification.data && e.notification.data.link) || self.registration.scope;
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
    const open = list.find(c => c.url.startsWith(self.registration.scope));
    return open ? open.focus() : self.clients.openWindow(link);
  }));
});
