(function (root, factory) {
  const core = factory();
  if (typeof module === "object" && module.exports) module.exports = core;
  else root.ManimSlidesPlayerCore = core;
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";

  const Status = Object.freeze({
    FAILED: "failed",
    HELD_END: "held-at-end",
    LOADING: "loading",
    PAUSED: "paused",
    PLAYING_FORWARD: "playing-forward",
    PLAYING_REVERSE: "playing-reverse",
    READY_START: "ready-at-start",
    TRANSITIONING: "transitioning",
  });

  function initial(slideCount) {
    return {
      active: null,
      animationOptIn: false,
      error: null,
      failedEffect: null,
      generation: 0,
      index: 0,
      pending: null,
      presenting: false,
      resumeStatus: null,
      slideCount,
      status: Status.LOADING,
    };
  }

  function unchanged(model) {
    return { model, effects: [] };
  }

  function mapReverseTime(forwardTime, forwardDuration, reverseDuration, tolerance = 0.15) {
    if (
      !Number.isFinite(forwardTime) ||
      !Number.isFinite(forwardDuration) ||
      !Number.isFinite(reverseDuration) ||
      forwardDuration <= 0 ||
      reverseDuration <= 0 ||
      Math.abs(reverseDuration - forwardDuration) / forwardDuration > tolerance
    ) {
      return { fallback: true, time: 0 };
    }
    const ratio = Math.max(0, Math.min(1, forwardTime / forwardDuration));
    return { fallback: false, time: reverseDuration * (1 - ratio) };
  }

  function load(model, details) {
    const generation = model.generation + 1;
    const effect = { ...details, type: "load", generation };
    return {
      model: {
        ...model,
        error: null,
        failedEffect: null,
        generation,
        pending: effect,
        resumeStatus: null,
        status: Status.TRANSITIONING,
      },
      effects: [effect],
    };
  }

  function transition(model, event, context = {}) {
    const slides = context.slides || [];
    const current = slides[model.index] || {};
    switch (event.type) {
      case "BOOT":
        if (!model.slideCount) return unchanged(model);
        return load(model, {
          autoplay: true,
          role: "forward",
          seek: "start",
          settleIndex: 0,
          slideIndex: 0,
        });
      case "NEXT":
        if (model.status === Status.TRANSITIONING && model.pending)
          return unchanged(model);
        if (
          model.status === Status.PLAYING_FORWARD ||
          model.status === Status.READY_START ||
          (model.status === Status.PAUSED &&
            model.resumeStatus === Status.PLAYING_FORWARD)
        ) {
          const generation = model.generation + 1;
          return {
            model: {
              ...model,
              generation,
              pending: null,
              status: Status.TRANSITIONING,
            },
            effects: [{ type: "hold", generation }],
          };
        }
        if (
          model.status === Status.PLAYING_REVERSE ||
          (model.status === Status.PAUSED && model.resumeStatus === Status.PLAYING_REVERSE)
        ) {
          return load(model, {
            autoplay: true,
            mapFromActive: true,
            role: "forward",
            seek: "mapped",
            settleIndex: model.index,
            slideIndex: model.index,
          });
        }
        if (model.index >= model.slideCount - 1) return unchanged(model);
        return load(model, {
          autoplay: true,
          role: "forward",
          seek: "start",
          settleIndex: model.index + 1,
          slideIndex: model.index + 1,
        });
      case "BACK":
        if (model.status === Status.TRANSITIONING) return unchanged(model);
        if (model.index <= 0) return unchanged(model);
        if (
          model.status === Status.PLAYING_REVERSE ||
          (model.status === Status.PAUSED &&
            model.resumeStatus === Status.PLAYING_REVERSE)
        ) {
          const generation = model.generation + 1;
          return {
            model: {
              ...model,
              generation,
              pending: null,
              status: Status.TRANSITIONING,
            },
            effects: [{ type: "hold", generation }],
          };
        }
        return load(model, {
          autoplay: true,
          mapFromActive:
            model.status === Status.PLAYING_FORWARD ||
            (model.status === Status.PAUSED && model.resumeStatus === Status.PLAYING_FORWARD),
          role: "reverse",
          seek: model.status === Status.HELD_END ? "start" : "mapped",
          settleIndex: model.index - 1,
          slideIndex: model.index,
        });
      case "REPLAY":
        return load({ ...model, animationOptIn: true }, {
          autoplay: true,
          role: "forward",
          seek: "start",
          settleIndex: model.index,
          slideIndex: model.index,
          userGesture: true,
        });
      case "JUMP": {
        const index = Math.max(0, Math.min(model.slideCount - 1, event.index));
        return load(model, {
          autoplay: false,
          role: "forward",
          seek: "end",
          settleIndex: index,
          slideIndex: index,
        });
      }
      case "TOGGLE_PAUSE":
        if (
          model.status === Status.PLAYING_FORWARD ||
          model.status === Status.PLAYING_REVERSE
        ) {
          return {
            model: {
              ...model,
              resumeStatus: model.status,
              status: Status.PAUSED,
            },
            effects: [{ type: "pause" }],
          };
        }
        if (model.status === Status.PAUSED && model.resumeStatus) {
          return {
            model: {
              ...model,
              animationOptIn: true,
              status: model.resumeStatus,
            },
            effects: [{ type: "play", userGesture: true }],
          };
        }
        return unchanged(model);
      case "PLAY_WITH_CONSENT":
        if (model.status !== Status.PAUSED || !model.resumeStatus)
          return unchanged(model);
        return {
          model: {
            ...model,
            animationOptIn: true,
            status: model.resumeStatus,
          },
          effects: [{ type: "play", userGesture: true }],
        };
      case "TOGGLE_PRESENT":
        if (model.presenting) {
          return {
            model: { ...model, presenting: false },
            effects: [{ type: "exit-fullscreen" }, { type: "focus-player" }],
          };
        }
        return {
          model: {
            ...model,
            animationOptIn: true,
            presenting: true,
            status:
              model.status === Status.PAUSED && model.resumeStatus
                ? model.resumeStatus
                : model.status,
          },
          effects: [
            ...(model.status === Status.PAUSED && model.resumeStatus
              ? [{ type: "play", userGesture: true }]
              : []),
            { type: "request-fullscreen" },
            { type: "focus-player" },
          ],
        };
      case "FULLSCREEN_EXITED":
        if (!model.presenting) return unchanged(model);
        return {
          model: { ...model, presenting: false },
          effects: [{ type: "focus-player" }],
        };
      case "LOAD_READY":
        if (event.generation !== model.generation || !model.pending)
          return unchanged(model);
        if (event.playable && event.requiresGesture && model.pending.autoplay) {
          return {
            model: {
              ...model,
              active: model.pending,
              index: model.pending.slideIndex,
              pending: null,
              resumeStatus:
                model.pending.role === "reverse"
                  ? Status.PLAYING_REVERSE
                  : Status.PLAYING_FORWARD,
              status: Status.PAUSED,
            },
            effects: [],
          };
        }
        if (!event.playable || !model.pending.autoplay) {
          return {
            model: {
              ...model,
              active: model.pending,
              index: model.pending.settleIndex,
              pending: null,
              status: Status.HELD_END,
            },
            effects: [],
          };
        }
        return {
          model: {
            ...model,
            active: model.pending,
            index: model.pending.slideIndex,
            pending: null,
            status:
              model.pending.role === "reverse"
                ? Status.PLAYING_REVERSE
                : Status.READY_START,
          },
          effects: [{ type: "play", generation: event.generation }],
        };
      case "PLAY_STARTED":
        if (event.generation !== model.generation || !model.active)
          return unchanged(model);
        return {
          model: {
            ...model,
            status:
              model.active.role === "reverse"
                ? Status.PLAYING_REVERSE
                : Status.PLAYING_FORWARD,
          },
          effects: [],
        };
      case "PLAY_REJECTED":
        if (event.generation !== model.generation) return unchanged(model);
        return {
          model: {
            ...model,
            resumeStatus:
              model.active && model.active.role === "reverse"
                ? Status.PLAYING_REVERSE
                : Status.PLAYING_FORWARD,
            status: Status.PAUSED,
          },
          effects: [],
        };
      case "HOLD_READY":
        if (event.generation !== model.generation) return unchanged(model);
        return {
          model: {
            ...model,
            index:
              model.active && model.active.role === "reverse"
                ? model.active.settleIndex
                : model.index,
            status: Status.HELD_END,
          },
          effects: [],
        };
      case "ENDED":
        if (event.generation !== model.generation || !model.active)
          return unchanged(model);
        if (model.active.role === "reverse") {
          return {
            model: {
              ...model,
              index: model.active.settleIndex,
              status: Status.HELD_END,
            },
            effects: [{ type: "hold-active" }],
          };
        }
        if (current.loop) {
          return {
            model: { ...model, status: Status.PLAYING_FORWARD },
            effects: [{ type: "replay-active" }],
          };
        }
        if (current.autoNext && model.index < model.slideCount - 1) {
          return load(model, {
            autoplay: true,
            role: "forward",
            seek: "start",
            settleIndex: model.index + 1,
            slideIndex: model.index + 1,
          });
        }
        return {
          model: { ...model, status: Status.HELD_END },
          effects: [{ type: "hold-active" }],
        };
      case "ERROR":
        if (event.generation !== model.generation) return unchanged(model);
        return {
          model: {
            ...model,
            error: event.message,
            failedEffect: model.pending || model.active,
            pending: null,
            status: Status.FAILED,
          },
          effects: [{ type: "pause" }],
        };
      case "RETRY":
        if (!model.failedEffect) return unchanged(model);
        return load(model, {
          autoplay: model.failedEffect.autoplay,
          mapFromActive: model.failedEffect.mapFromActive,
          role: model.failedEffect.role,
          seek: model.failedEffect.seek,
          settleIndex: model.failedEffect.settleIndex,
          slideIndex: model.failedEffect.slideIndex,
        });
      default:
        return unchanged(model);
    }
  }

  return { Status, initial, mapReverseTime, transition };
});
