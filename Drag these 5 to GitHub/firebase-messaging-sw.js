/* Éanna Media Calendar: receives notifications on phones and laptops, even when the site is closed.
   Keep this file next to index.html on GitHub. */
importScripts("https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyAsWri-GSXMJVGg1Q3eKVsOKC6JQtCTQl4",
  authDomain: "eanna-media-calendar.firebaseapp.com",
  projectId: "eanna-media-calendar",
  storageBucket: "eanna-media-calendar.firebasestorage.app",
  messagingSenderId: "364025776600",
  appId: "1:364025776600:web:474dc0ac15931bf39dcaad"
});

// Notifications sent with a title and message are shown automatically,
// and tapping one opens the calendar (the link comes with the notification).
firebase.messaging();
