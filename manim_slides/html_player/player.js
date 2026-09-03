(function () {
  "use strict";

  const Core = globalThis.ManimSlidesPlayerCore;
  if (!Core) throw new Error("Manim Slides player core did not load.");

  class AssetStore {
    constructor(root, limit = 6) {
      this.root = root;
      this.limit = limit;
      this.urls = new Map();
    }

    get(asset) {
      if (asset.storage === "file") return asset.url;
      if (this.urls.has(asset.id)) {
        const url = this.urls.get(asset.id);
        this.urls.delete(asset.id);
        this.urls.set(asset.id, url);
        return url;
      }
      const node = this.root.querySelector(
        `[data-ms-asset="${CSS.escape(asset.id)}"]`,
      );
      if (!node) throw new Error(`Embedded asset '${asset.id}' is missing.`);
      const base64 = node.textContent.trim();
      const parts = [];
      const chunkSize = 1024 * 1024 - ((1024 * 1024) % 4);
      for (let offset = 0; offset < base64.length; offset += chunkSize) {
        const binary = atob(base64.slice(offset, offset + chunkSize));
        const bytes = Uint8Array.from(binary, (character) =>
          character.charCodeAt(0),
        );
        parts.push(bytes);
      }
      // eslint-disable-next-line compat/compat -- Self-contained media requires Blob URLs.
      const url = URL.createObjectURL(
        new Blob(parts, { type: asset.mimeType }),
      );
      this.urls.set(asset.id, url);
      return url;
    }

    trim(protectedIds = new Set()) {
      for (const [id, url] of this.urls) {
        if (this.urls.size <= this.limit) break;
        if (protectedIds.has(id)) continue;
        // eslint-disable-next-line compat/compat -- Blob URL support is required above.
        URL.revokeObjectURL(url);
        this.urls.delete(id);
      }
    }

    destroy() {
      for (const url of this.urls.values()) {
        // eslint-disable-next-line compat/compat -- Blob URL support is required above.
        URL.revokeObjectURL(url);
      }
      this.urls.clear();
    }
  }

  class Player {
    constructor(root) {
      this.root = root;
      this.manifest = JSON.parse(
        root.querySelector("[data-ms-manifest]").textContent,
      );
      if (this.manifest.version !== 1) {
        throw new Error(
          `Unsupported player manifest version '${this.manifest.version}'.`,
        );
      }
      this.slides = this.manifest.slides;
      this.model = Core.initial(this.slides.length);
      this.assetStore = new AssetStore(root);
      this.slots = [...root.querySelectorAll("[data-ms-slot]")].map((node) => ({
        node,
        video: node.querySelector("video"),
        image: node.querySelector("img"),
        assetId: null,
      }));
      this.activeSlot = 0;
      this.loading = root.querySelector("[data-ms-loading]");
      this.gesture = root.querySelector("[data-ms-gesture]");
      this.error = root.querySelector("[data-ms-error]");
      this.errorMessage = root.querySelector("[data-ms-error-message]");
      this.position = root.querySelector("[data-ms-position]");
      this.progress = root.querySelector("[data-ms-progress]");
      this.notes = root.querySelector("[data-ms-notes]");
      this.notesText = root.querySelector("[data-ms-notes-text]");
      this.help = root.querySelector("[data-ms-help]");
      this.overview = root.querySelector("[data-ms-overview]");
      this.overviewList = root.querySelector("[data-ms-overview-list]");
      this.reducedMotion = matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      this.abort = new AbortController();
      this.pointer = null;
      this.suppressClick = false;
      this.buildOverview();
      this.bindInputs();
      this.render();
      this.dispatch({ type: "BOOT" });
    }

    dispatch(event) {
      const result = Core.transition(this.model, event, {
        slides: this.slides,
      });
      this.model = result.model;
      this.render();
      for (const effect of result.effects) this.run(effect);
    }

    run(effect) {
      if (effect.type === "load") this.load(effect);
      else if (effect.type === "play") this.play(effect);
      else if (effect.type === "pause") this.currentVideo()?.pause();
      else if (effect.type === "hold") this.hold(effect);
      else if (effect.type === "hold-active") this.holdActive();
      else if (effect.type === "replay-active") this.replayActive();
      else if (effect.type === "request-fullscreen")
        this.requestPresentationFullscreen();
      else if (effect.type === "exit-fullscreen")
        this.exitPresentationFullscreen();
      else if (effect.type === "focus-player")
        this.root.focus({ preventScroll: true });
    }

    currentSlot() {
      return this.slots[this.activeSlot];
    }

    currentVideo() {
      const slot = this.currentSlot();
      return slot.node.classList.contains("is-video") ? slot.video : null;
    }

    safeEnd(video) {
      return Number.isFinite(video.duration)
        ? Math.max(0, video.duration - 0.001)
        : 0;
    }

    waitFor(target, name, generation, rejectName = "error") {
      // eslint-disable-next-line compat/compat -- The player targets modern browsers.
      return new Promise((resolve, reject) => {
        const done = () => {
          cleanup();
          if (generation !== this.model.generation)
            reject(new DOMException("Stale operation", "AbortError"));
          else resolve();
        };
        const failed = () => {
          cleanup();
          reject(new Error(`${rejectName} while loading media`));
        };
        const cleanup = () => {
          target.removeEventListener(name, done);
          target.removeEventListener(rejectName, failed);
        };
        target.addEventListener(name, done, { once: true });
        target.addEventListener(rejectName, failed, { once: true });
      });
    }

    async seek(video, time, generation) {
      const target = Math.max(0, Math.min(this.safeEnd(video), time));
      if (Math.abs(video.currentTime - target) < 0.002) return;
      const ready = this.waitFor(video, "seeked", generation);
      video.currentTime = target;
      await ready;
      if ("requestVideoFrameCallback" in video) {
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(resolve, 180);
          video.requestVideoFrameCallback(() => {
            clearTimeout(timeout);
            if (generation !== this.model.generation)
              reject(new DOMException("Stale operation", "AbortError"));
            else resolve();
          });
        });
      } else {
        await new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        );
      }
    }

    mappedTime(effect, duration) {
      if (!effect.mapFromActive) return 0;
      const active = this.currentVideo();
      if (!active || !Number.isFinite(active.duration) || active.duration <= 0)
        return 0;
      const mapping = Core.mapReverseTime(
        active.currentTime,
        active.duration,
        duration,
      );
      if (mapping.fallback) {
        this.loading.textContent =
          "Media durations differ; using full reverse playback.";
      }
      return mapping.time;
    }

    async load(effect) {
      const generation = effect.generation;
      const slide = this.slides[effect.slideIndex];
      const asset = slide[effect.role];
      const slotIndex = 1 - this.activeSlot;
      const slot = slotIndex === 0 ? this.slots[0] : this.slots[1];
      this.loading.hidden = false;
      this.loading.textContent = `Loading slide ${effect.slideIndex + 1} (${effect.role})…`;
      this.gesture.hidden = true;
      this.error.hidden = true;
      slot.video.pause();
      slot.video.removeAttribute("src");
      slot.image.removeAttribute("src");
      slot.node.classList.remove("is-video", "is-image");
      try {
        const url = this.assetStore.get(asset);
        if (asset.kind === "image") {
          slot.node.classList.add("is-image");
          const loaded = this.waitFor(slot.image, "load", generation);
          slot.image.src = url;
          await loaded;
          if (slot.image.decode) await slot.image.decode();
        } else {
          slot.node.classList.add("is-video");
          slot.video.muted = false;
          slot.video.playbackRate =
            effect.role === "reverse"
              ? slide.reversedPlaybackRate
              : slide.playbackRate;
          const metadata = this.waitFor(
            slot.video,
            "loadedmetadata",
            generation,
          );
          slot.video.src = url;
          slot.video.load();
          await metadata;
          let target = 0;
          if (effect.seek === "end") target = this.safeEnd(slot.video);
          else if (effect.seek === "mapped")
            target = this.mappedTime(effect, slot.video.duration);
          await this.seek(slot.video, target, generation);
        }
        if (generation !== this.model.generation) return;
        slot.assetId = asset.id;
        this.applySlideAppearance(slide);
        this.slots[this.activeSlot].node.classList.remove("is-active");
        slot.node.classList.add("is-active");
        this.activeSlot = slotIndex;
        const protectedIds = new Set(
          this.slots.map((item) => item.assetId).filter(Boolean),
        );
        this.assetStore.trim(protectedIds);
        this.loading.hidden = true;
        this.dispatch({
          type: "LOAD_READY",
          generation,
          playable: asset.kind === "video",
          requiresGesture:
            asset.kind === "video" &&
            this.reducedMotion &&
            effect.autoplay &&
            !this.model.animationOptIn,
        });
      } catch (error) {
        if (error && error.name === "AbortError") return;
        this.dispatch({
          type: "ERROR",
          generation,
          message: `Slide ${effect.slideIndex + 1} ${effect.role} asset '${asset.id}' could not be loaded: ${error.message || error}`,
        });
      }
    }

    applySlideAppearance(slide) {
      const [width, height] = slide.resolution;
      this.root.style.setProperty("--ms-background", slide.backgroundColor);
      this.root.style.setProperty("--ms-fit", this.manifest.backgroundSize);
      this.root.style.aspectRatio = `${width} / ${height}`;
    }

    async play(effect) {
      const video = this.currentVideo();
      const generation = effect.generation ?? this.model.generation;
      if (!video) return;
      video.onended = () => this.dispatch({ type: "ENDED", generation });
      video.onerror = () =>
        this.dispatch({
          type: "ERROR",
          generation,
          message: `Slide ${this.model.index + 1} media decoding failed.`,
        });
      try {
        await video.play();
        this.dispatch({ type: "PLAY_STARTED", generation });
      } catch (error) {
        this.dispatch({ type: "PLAY_REJECTED", generation });
      }
    }

    async hold(effect) {
      const video = this.currentVideo();
      if (video) {
        video.pause();
        try {
          await this.seek(video, this.safeEnd(video), effect.generation);
        } catch (error) {
          if (error.name === "AbortError") return;
        }
      }
      this.dispatch({ type: "HOLD_READY", generation: effect.generation });
    }

    holdActive() {
      const video = this.currentVideo();
      if (!video) return;
      video.pause();
      if (Number.isFinite(video.duration))
        video.currentTime = this.safeEnd(video);
    }

    replayActive() {
      const video = this.currentVideo();
      if (!video) return;
      video.currentTime = 0;
      this.play({ generation: this.model.generation });
    }

    async requestPresentationFullscreen() {
      if (
        !this.root.requestFullscreen ||
        document.fullscreenElement === this.root
      )
        return;
      try {
        await this.root.requestFullscreen();
        if (!this.model.presenting && document.fullscreenElement === this.root)
          await document.exitFullscreen?.();
      } catch (_error) {
        // Present mode remains useful when fullscreen is unavailable or denied.
      }
    }

    async exitPresentationFullscreen() {
      if (document.fullscreenElement !== this.root || !document.exitFullscreen)
        return;
      try {
        await document.exitFullscreen();
      } catch (_error) {
        // The fullscreenchange handler remains the source of synchronization.
      }
    }

    render() {
      const slide = this.slides[this.model.index];
      const total = this.slides.length;
      this.root.dataset.state = this.model.status;
      this.root.dataset.slideIndex = String(this.model.index);
      this.root.dataset.animationOptIn = String(this.model.animationOptIn);
      this.root.dataset.presenting = String(this.model.presenting);
      this.root.classList.toggle("is-presenting", this.model.presenting);
      this.position.textContent = total
        ? `${this.model.index + 1} / ${total}`
        : "0 / 0";
      this.progress.max = Math.max(1, total - 1);
      this.progress.value = this.model.index;
      this.notesText.textContent = slide ? slide.notes : "";
      this.error.hidden = this.model.status !== Core.Status.FAILED;
      if (this.model.error) this.errorMessage.textContent = this.model.error;
      const needsGesture =
        this.model.status === Core.Status.PAUSED &&
        this.model.resumeStatus !== null;
      this.gesture.hidden = !needsGesture;
      if (needsGesture)
        this.gesture.textContent = this.reducedMotion
          ? "Play animation"
          : "Play presentation";
      const forwardWillFinish =
        this.model.status === Core.Status.PLAYING_FORWARD ||
        this.model.status === Core.Status.READY_START ||
        (this.model.status === Core.Status.PAUSED &&
          this.model.resumeStatus === Core.Status.PLAYING_FORWARD);
      this.root
        .querySelector("nav [data-command=next]")
        .setAttribute(
          "aria-label",
          forwardWillFinish ? "Finish current animation" : "Next slide",
        );
      for (const button of this.overviewList.querySelectorAll("button"))
        button.setAttribute(
          "aria-current",
          String(Number(button.dataset.index) === this.model.index),
        );
    }

    buildOverview() {
      this.slides.forEach((slide, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.index = String(index);
        button.textContent = `Slide ${index + 1}${slide.direction === "vertical" ? " ↓" : ""}`;
        button.addEventListener("click", () => {
          this.overview.hidden = true;
          this.root.focus({ preventScroll: true });
          this.dispatch({ type: "JUMP", index });
        });
        this.overviewList.append(button);
      });
    }

    command(name) {
      if (name === "next") this.dispatch({ type: "NEXT" });
      else if (name === "back") this.dispatch({ type: "BACK" });
      else if (name === "replay") this.dispatch({ type: "REPLAY" });
      else if (name === "pause") this.dispatch({ type: "TOGGLE_PAUSE" });
      else if (name === "notes") this.notes.hidden = !this.notes.hidden;
      else if (name === "overview")
        this.overview.hidden = !this.overview.hidden;
      else if (name === "help") this.help.hidden = !this.help.hidden;
      else if (name === "present") this.dispatch({ type: "TOGGLE_PRESENT" });
    }

    closeOverlays() {
      if (!this.help.hidden || !this.overview.hidden || !this.notes.hidden) {
        this.help.hidden = true;
        this.overview.hidden = true;
        this.notes.hidden = true;
        return true;
      }
      return false;
    }

    bindInputs() {
      const signal = this.abort.signal;
      this.root.addEventListener(
        "keydown",
        (event) => {
          if (
            event.target.closest("input, textarea, select, [contenteditable]")
          )
            return;
          const map = {
            " ": "next",
            ArrowRight: "next",
            PageDown: "next",
            ArrowLeft: "back",
            PageUp: "back",
            r: "replay",
            R: "replay",
            p: "pause",
            P: "pause",
            n: "notes",
            N: "notes",
            o: "overview",
            O: "overview",
            f: "present",
            F: "present",
            "?": "help",
          };
          if (event.key === "Escape") {
            if (this.closeOverlays()) event.preventDefault();
            else if (this.model.presenting) {
              event.preventDefault();
              this.dispatch({ type: "TOGGLE_PRESENT" });
            }
            return;
          }
          const command = map[event.key];
          if (command) {
            event.preventDefault();
            this.command(command);
          }
        },
        { signal },
      );
      this.root.querySelectorAll("[data-command]").forEach((button) =>
        button.addEventListener(
          "click",
          (event) => {
            event.stopPropagation();
            this.command(button.dataset.command);
          },
          { signal },
        ),
      );
      this.root.querySelector("[data-ms-retry]").addEventListener(
        "click",
        (event) => {
          event.stopPropagation();
          this.dispatch({ type: "RETRY" });
        },
        { signal },
      );
      this.gesture.addEventListener(
        "click",
        (event) => {
          event.stopPropagation();
          this.root.focus({ preventScroll: true });
          this.dispatch({ type: "PLAY_WITH_CONSENT" });
        },
        { signal },
      );
      const stage = this.root.querySelector("[data-ms-stage]");
      stage.addEventListener(
        "pointerdown",
        (event) => this.pointerDown(event),
        { signal },
      );
      stage.addEventListener(
        "pointermove",
        (event) => this.pointerMove(event),
        { signal },
      );
      stage.addEventListener("pointerup", (event) => this.pointerUp(event), {
        signal,
      });
      stage.addEventListener(
        "pointercancel",
        () => {
          this.pointer = null;
        },
        { signal },
      );
      stage.addEventListener(
        "click",
        (event) => {
          if (this.suppressClick) {
            this.suppressClick = false;
            return;
          }
          if (
            event.button === 0 &&
            !event.target.closest("button, a, input, select, textarea")
          ) {
            this.root.focus({ preventScroll: true });
            this.command("next");
          }
        },
        { signal },
      );
      if (this.root.hasAttribute("data-ms-standalone"))
        this.root.focus({ preventScroll: true });
      document.addEventListener(
        "fullscreenchange",
        () => {
          if (this.model.presenting && document.fullscreenElement !== this.root)
            this.dispatch({ type: "FULLSCREEN_EXITED" });
        },
        { signal },
      );
      addEventListener("pagehide", () => this.destroy(), {
        once: true,
        signal,
      });
    }

    pointerDown(event) {
      if (!event.isPrimary || event.button !== 0) return;
      this.pointer = {
        id: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        lastX: event.clientX,
        lastY: event.clientY,
        time: event.timeStamp,
        lastTime: event.timeStamp,
      };
    }

    pointerMove(event) {
      if (!this.pointer || event.pointerId !== this.pointer.id) return;
      this.pointer.lastX = event.clientX;
      this.pointer.lastY = event.clientY;
      this.pointer.lastTime = event.timeStamp;
    }

    pointerUp(event) {
      if (!this.pointer || event.pointerId !== this.pointer.id) return;
      const pointer = this.pointer;
      this.pointer = null;
      const dx = event.clientX - pointer.x;
      const dy = event.clientY - pointer.y;
      const elapsed = Math.max(1, event.timeStamp - pointer.time);
      const distance = Math.hypot(dx, dy);
      const velocity = distance / elapsed;
      if (distance < 48 || velocity < 0.25) return;
      let command = null;
      if (Math.abs(dx) >= Math.abs(dy)) command = dx < 0 ? "next" : "back";
      else if (
        dy < 0 &&
        this.slides[this.model.index + 1]?.direction === "vertical"
      )
        command = "next";
      else if (
        dy > 0 &&
        this.slides[this.model.index]?.direction === "vertical"
      )
        command = "back";
      if (command) {
        this.suppressClick = true;
        this.root.focus({ preventScroll: true });
        this.command(command);
      }
    }

    destroy() {
      this.abort.abort();
      for (const slot of this.slots) {
        slot.video.pause();
        slot.video.removeAttribute("src");
        slot.image.removeAttribute("src");
      }
      this.assetStore.destroy();
    }
  }

  for (const root of document.querySelectorAll("[data-ms-player]")) {
    try /* NOPMD - Each player needs an isolated initialization failure boundary. */ {
      root.manimSlidesPlayer = new Player(root);
    } catch (error) {
      const status = root.querySelector("[data-ms-loading]");
      if (status)
        status.textContent = `Player initialization failed: ${error.message || error}`;
      root.dataset.state = "failed";
    }
  }
})();
