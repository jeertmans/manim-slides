"""Script to re-generate firebase_sync.html from revealjs.html."""

import sys
from pathlib import Path

HEAD_INSERT = """\
    <!-- FIREBASE REALTIME DATABASE SYNC -->
    <script type="module">
      import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
      import { getAuth, signInAnonymously } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
      import { getDatabase, ref, onValue, set, serverTimestamp, onDisconnect } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-database.js";

      const firebaseConfig = {
        apiKey: "{{ firebase_api_key | default('AIzaSyD6zkJUPgUF0X5jgLo_E2lOSIUXvNPi5Xk') }}",
        authDomain: "{{ firebase_auth_domain | default('manim-slides-sync.firebaseapp.com') }}",
        databaseURL: "{{ firebase_database_url | default('https://manim-slides-sync-default-rtdb.europe-west1.firebasedatabase.app') }}",
        projectId: "{{ firebase_project_id | default('manim-slides-sync') }}"
      };

      const params = new URLSearchParams(window.location.search);
      const hash = window.location.hash;
      const role = (params.get("role") === "presenter" || hash.includes("presenter")) ? "presenter" : "guest";

      const isPresenter = role === "presenter";
      const isGuest = !isPresenter;

      let roomId = params.get("room");
      if (isPresenter && !roomId) {
        roomId = "room-" + Math.random().toString(36).substring(2, 8);
        params.set("room", roomId);
        const newUrl = window.location.pathname + "?" + params.toString() + hash;
        window.history.replaceState(null, "", newUrl);
      }

      if (roomId) {
        const app = initializeApp(firebaseConfig);
        const auth = getAuth(app);
        const db = getDatabase(app);
        const roomRef = ref(db, `rooms/${roomId}`);
        const metaRef = ref(db, `rooms/${roomId}/meta`);

        let lastSeq = 0;
        let revealReady = typeof Reveal !== "undefined" && Reveal.isReady && Reveal.isReady();
        let bufferedUpdate = null;

        if (isPresenter) {
          const showControls = () => {
            const controls = document.getElementById("presenter-controls");
            if (controls) controls.style.display = "flex";
          };
          if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", showControls);
          } else {
            showControls();
          }

          signInAnonymously(auth).then(() => {
            const uid = auth.currentUser.uid;
            // Optional: Write presenter ID for security rules
            set(metaRef, { presenterId: uid });

            // Clean up the room when the presenter disconnects/closes the page
            onDisconnect(roomRef).remove();

            let lastPointerUpdate = 0;
            document.addEventListener('mousemove', (e) => {
              const now = Date.now();
              if (now - lastPointerUpdate > 100) {
                lastPointerUpdate = now;
                const x = e.clientX / window.innerWidth;
                const y = e.clientY / window.innerHeight;
                set(ref(db, `rooms/${roomId}/pointer`), { x, y, active: true });
              }
            });
            document.addEventListener('mouseleave', () => {
              set(ref(db, `rooms/${roomId}/pointer`), { active: false });
            });

            window._sendFirebaseSlideState = function(indices = null) {
              if (!indices && typeof Reveal !== "undefined" && Reveal.getIndices) {
                indices = Reveal.getIndices();
              }
              if (indices) {
                lastSeq++;
                const payload = {
                  h: indices.h || 0,
                  v: indices.v || 0,
                  f: indices.f || 0,
                  seq: lastSeq,
                  updatedAt: serverTimestamp(),
                  meta: { presenterId: uid }
                };
                console.log("Firebase sending sync update:", { ...payload, updatedAt: "serverTimestamp()" });
                set(roomRef, payload);
              }
            };

            if (typeof Reveal !== "undefined") {
              if (Reveal.isReady()) {
                window._sendFirebaseSlideState();
              } else {
                Reveal.on("ready", () => window._sendFirebaseSlideState());
              }
              Reveal.on("slidechanged", () => window._sendFirebaseSlideState());
            } else {
              // Wait for Reveal to become available
              window.addEventListener("load", () => {
                Reveal.on("ready", () => window._sendFirebaseSlideState());
                Reveal.on("slidechanged", () => window._sendFirebaseSlideState());
              });
            }
          }).catch((err) => console.error("Firebase Auth Error", err));
        } else {
          // Guest mode
          onValue(roomRef, (snapshot) => {
            const data = snapshot.val();
            console.log("Firebase received sync event:", data);
            if (data && data.seq > lastSeq) {
              lastSeq = data.seq;
              if (revealReady && typeof Reveal !== "undefined") {
                Reveal.slide(data.h, data.v, data.f);
              } else {
                bufferedUpdate = data;
              }
            }
          });

          // Handlers to apply update once Reveal is ready
          const onRevealReady = () => {
            revealReady = true;
            if (bufferedUpdate) {
              Reveal.slide(bufferedUpdate.h, bufferedUpdate.v, bufferedUpdate.f);
              bufferedUpdate = null;
            }
            // Disable guest controls
            Reveal.configure({
              controls: false,
              progress: false,
              keyboard: false,
              touch: false,
              overview: false,
              mouseWheel: false,
            });
          };

          if (typeof Reveal !== "undefined") {
            if (Reveal.isReady()) onRevealReady();
            else Reveal.on("ready", onRevealReady);
          } else {
            window.addEventListener("load", () => {
              if (Reveal.isReady()) onRevealReady();
              else Reveal.on("ready", onRevealReady);
            });
          }

          // Laser pointer setup
          const laser = document.createElement("div");
          laser.style.position = "fixed";
          laser.style.left = "0px";
          laser.style.top = "0px";
          laser.style.width = "15px";
          laser.style.height = "15px";
          laser.style.borderRadius = "50%";
          laser.style.backgroundColor = "red";
          laser.style.boxShadow = "0 0 10px red";
          laser.style.zIndex = "99999";
          laser.style.pointerEvents = "none";
          laser.style.transition = "transform 0.05s linear, opacity 0.2s";
          laser.style.opacity = "0";
          document.body.appendChild(laser);

          let hideTimeout;
          onValue(ref(db, `rooms/${roomId}/pointer`), (snapshot) => {
            const data = snapshot.val();
            if (data && data.active !== false) {
              laser.style.opacity = "1";
              laser.style.transform = `translate(${data.x * window.innerWidth}px, ${data.y * window.innerHeight}px) translate(-50%, -50%)`;
              clearTimeout(hideTimeout);
              hideTimeout = setTimeout(() => { laser.style.opacity = "0"; }, 1500);
            } else {
              laser.style.opacity = "0";
            }
          });
        }
      }
    </script>
"""

BODY_INSERT = """\
    <!-- Presenter Controls -->
    <div id="presenter-controls" style="position: fixed; top: 10px; right: 12px; z-index: 9999; display: none; gap: 8px; align-items: center;">
      <button
        id="copy-guest-link"
        style="font-size: 12px; color: #fff; background: rgba(0, 0, 0, 0.45); padding: 4px 8px; border-radius: 4px; border: 1px solid #555; cursor: pointer;"
        onclick="const btn = this; let link = window.location.href.split('#')[0].replace(/([?&])role=presenter(&|$)/, '$1').replace(/[?&]$/, '') + '#guest'; navigator.clipboard.writeText(link).then(() => { const old = btn.innerText; btn.innerText = 'Copied!'; setTimeout(() => btn.innerText = old, 1500); })"
      >Copy Guest Link</button>
    </div>
"""


def main() -> None:
    root = Path(__file__).parent.parent
    templates_dir = root / "manim_slides" / "templates"

    revealjs_file = templates_dir / "revealjs.html"
    firebase_sync_file = templates_dir / "firebase_sync.html"

    if not revealjs_file.exists():
        # print(f"Error: {revealjs_file} not found.")
        sys.exit(1)

    revealjs_content = revealjs_file.read_text(encoding="utf-8")

    new_content = revealjs_content.replace(
        "  </head>", f"{HEAD_INSERT}  </head>"
    ).replace("  <body>", f"  <body>\n{BODY_INSERT}")

    file_changed = False
    if firebase_sync_file.exists():
        existing_content = firebase_sync_file.read_text(encoding="utf-8")
        if existing_content != new_content:
            file_changed = True
    else:
        file_changed = True

    if file_changed:
        firebase_sync_file.write_text(new_content, encoding="utf-8")
        # print("Updated firebase_sync.html")
        sys.exit(1)


if __name__ == "__main__":
    main()
