"""Send the Éanna Media Calendar's waiting notifications to phones.

GitHub runs this every few minutes (.github/workflows/notify.yml). The site saves
each thing worth a notification (a new idea, a chat message...) as a waiting
item. This script sends each one to everyone who switched that kind on, then
deletes it, and drops any phone that has turned notifications off.

Needs the FIREBASE_SERVICE_ACCOUNT secret: the JSON key from Firebase
(Project settings > Service accounts > Generate new private key).
"""
import json
import os
import sys

import firebase_admin
from firebase_admin import credentials, firestore, messaging

key = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip()
if not key:
    sys.exit("The FIREBASE_SERVICE_ACCOUNT secret is missing. Add it in the repo's Settings > Secrets and variables > Actions.")

firebase_admin.initialize_app(credentials.Certificate(json.loads(key)))
db = firestore.client()


def site_url():
    """The calendar's address, worked out from the repo name (or SITE_URL if set)."""
    url = os.environ.get("SITE_URL", "").strip()
    if url:
        return url if url.endswith("/") else url + "/"
    owner, _, repo = os.environ.get("GITHUB_REPOSITORY", "").partition("/")
    if not owner:
        return ""
    if repo.lower() == f"{owner.lower()}.github.io":
        return f"https://{owner.lower()}.github.io/"
    return f"https://{owner.lower()}.github.io/{repo}/"


URL = site_url()
settings_ref = db.collection("config").document("settings")
notify = (settings_ref.get().to_dict() or {}).get("notify") or {}

waiting = sorted(db.collection("items").where("kind", "==", "evt").stream(),
                 key=lambda d: (d.to_dict() or {}).get("at", 0))
if not waiting:
    print("Nothing to send.")
    sys.exit(0)


def tokens_of(cfg):
    return [t["t"] if isinstance(t, dict) else t for t in (cfg.get("webTokens") or []) if t]


gone = {}  # person id -> tokens that no longer work
sent = 0
for snap in waiting:
    ev = snap.to_dict() or {}
    kind, actor, only, own = ev.get("ev"), ev.get("actor"), ev.get("only"), ev.get("self")
    for pid, cfg in notify.items():
        if not isinstance(cfg, dict):
            continue
        if only and pid != only:
            continue
        if not own and (pid == actor or not (cfg.get("on") or {}).get(kind)):
            continue
        toks = tokens_of(cfg)
        if not toks:
            continue
        msg = messaging.MulticastMessage(
            tokens=toks,
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=ev.get("title") or "Éanna Media Calendar",
                    body=(ev.get("message") or "")[:300],
                    icon=(URL + "icon-192.png") if URL else None,
                ),
                fcm_options=messaging.WebpushFCMOptions(link=URL) if URL else None,
            ),
        )
        res = messaging.send_each_for_multicast(msg)
        sent += res.success_count
        for tok, r in zip(toks, res.responses):
            if not r.success and isinstance(r.exception, (messaging.UnregisteredError, messaging.SenderIdMismatchError)):
                gone.setdefault(pid, set()).add(tok)
            elif not r.success:
                print(f"Couldn't send to one of {pid}'s devices: {r.exception}")
    snap.reference.delete()

# Forget phones that have switched notifications off or been reset
for pid, dead in gone.items():
    cur = (notify.get(pid) or {}).get("webTokens") or []
    keep = [t for t in cur if (t["t"] if isinstance(t, dict) else t) not in dead]
    settings_ref.update({db.field_path("notify", pid, "webTokens"): keep})

print(f"Sent {sent} notification(s) for {len(waiting)} update(s).")
