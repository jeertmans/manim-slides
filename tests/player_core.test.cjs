const assert = require("node:assert/strict");
const test = require("node:test");
const Core = require("../manim_slides/html_player/player-core.js");

const slides = [
  { autoNext: false, loop: false },
  { autoNext: false, loop: false },
  { autoNext: true, loop: false },
];

function apply(model, event) {
  return Core.transition(model, event, { slides });
}

function loadedForward(index = 0) {
  let model = Core.initial(slides.length);
  let result = apply(model, { type: "BOOT" });
  model = result.model;
  result = apply(model, { type: "LOAD_READY", generation: model.generation, playable: true });
  model = result.model;
  result = apply(model, { type: "PLAY_STARTED", generation: model.generation });
  model = result.model;
  if (index) {
    result = apply(model, { type: "JUMP", index });
    model = result.model;
    result = apply(model, { type: "LOAD_READY", generation: model.generation, playable: false });
    model = result.model;
  }
  return model;
}

test("normal forward, held, next, reverse, and direct jump transitions", () => {
  let model = loadedForward();
  assert.equal(model.status, Core.Status.PLAYING_FORWARD);
  let result = apply(model, { type: "ENDED", generation: model.generation });
  model = result.model;
  assert.equal(model.status, Core.Status.HELD_END);
  result = apply(model, { type: "NEXT" });
  assert.equal(result.effects[0].slideIndex, 1);
  model = result.model;
  result = apply(model, { type: "LOAD_READY", generation: model.generation, playable: true });
  model = result.model;
  result = apply(model, { type: "PLAY_STARTED", generation: model.generation });
  model = result.model;
  result = apply(model, { type: "ENDED", generation: model.generation });
  model = result.model;
  result = apply(model, { type: "BACK" });
  assert.equal(result.effects[0].role, "reverse");
  assert.equal(result.effects[0].slideIndex, 1);
  model = result.model;
  result = apply(model, { type: "LOAD_READY", generation: model.generation, playable: true });
  model = result.model;
  result = apply(model, { type: "PLAY_STARTED", generation: model.generation });
  model = result.model;
  result = apply(model, { type: "ENDED", generation: model.generation });
  assert.equal(result.model.index, 0);
  assert.equal(result.model.status, Core.Status.HELD_END);
  result = apply(result.model, { type: "JUMP", index: 2 });
  assert.equal(result.effects[0].seek, "end");
});

test("partial reversal mapping and duration mismatch fallback are deterministic", () => {
  assert.deepEqual(Core.mapReverseTime(2, 4, 4), { fallback: false, time: 2 });
  assert.deepEqual(Core.mapReverseTime(2, 4, 7), { fallback: true, time: 0 });
  const model = loadedForward(1);
  const playing = { ...model, status: Core.Status.PLAYING_FORWARD };
  const result = apply(playing, { type: "BACK" });
  assert.equal(result.effects[0].seek, "mapped");
  assert.equal(result.effects[0].mapFromActive, true);
});

test("replay and pause resume preserve semantic role", () => {
  let model = loadedForward();
  let result = apply(model, { type: "TOGGLE_PAUSE" });
  model = result.model;
  assert.equal(model.status, Core.Status.PAUSED);
  assert.equal(model.resumeStatus, Core.Status.PLAYING_FORWARD);
  result = apply(model, { type: "TOGGLE_PAUSE" });
  assert.equal(result.model.status, Core.Status.PLAYING_FORWARD);
  result = apply(result.model, { type: "REPLAY" });
  assert.equal(result.effects[0].seek, "start");
  assert.equal(result.effects[0].slideIndex, 0);
  assert.equal(result.effects[0].userGesture, true);
});

test("reduced motion waits in the existing paused state for explicit playback", () => {
  let model = Core.initial(slides.length);
  let result = apply(model, { type: "BOOT" });
  model = result.model;
  result = apply(model, {
    type: "LOAD_READY",
    generation: model.generation,
    playable: true,
    requiresGesture: true,
  });
  model = result.model;
  assert.equal(model.status, Core.Status.PAUSED);
  assert.equal(model.resumeStatus, Core.Status.PLAYING_FORWARD);
  assert.equal(result.effects.length, 0);

  result = apply(model, { type: "TOGGLE_PAUSE" });
  assert.equal(result.model.status, Core.Status.PLAYING_FORWARD);
  assert.deepEqual(result.effects, [{ type: "play", userGesture: true }]);
});

test("first and last boundaries are quiet", () => {
  let model = loadedForward();
  let result = apply({ ...model, status: Core.Status.HELD_END }, { type: "BACK" });
  assert.equal(result.effects.length, 0);
  model = loadedForward(2);
  result = apply(model, { type: "NEXT" });
  assert.equal(result.effects.length, 0);
});

test("stale completions and rapid next back next cannot win", () => {
  let model = loadedForward(1);
  let result = apply(model, { type: "BACK" });
  const stale = result.model.generation;
  model = result.model;
  result = apply(model, { type: "NEXT" });
  model = result.model;
  result = apply(model, { type: "BACK" });
  model = result.model;
  result = apply(model, { type: "NEXT" });
  model = result.model;
  const ignored = apply(model, { type: "LOAD_READY", generation: stale, playable: true });
  assert.strictEqual(ignored.model, model);
  assert.ok(model.generation > stale);
});

test("loop, auto-next, error, and retry effects are explicit", () => {
  let model = loadedForward(1);
  model = { ...model, active: { role: "forward", settleIndex: 1, slideIndex: 1 } };
  let result = Core.transition(model, { type: "ENDED", generation: model.generation }, {
    slides: [slides[0], { autoNext: false, loop: true }, slides[2]],
  });
  assert.equal(result.effects[0].type, "replay-active");
  model = loadedForward(1);
  result = apply(model, { type: "NEXT" });
  model = result.model;
  const generation = model.generation;
  result = apply(model, { type: "ERROR", generation, message: "decode failed" });
  assert.equal(result.model.status, Core.Status.FAILED);
  result = apply(result.model, { type: "RETRY" });
  assert.equal(result.effects[0].type, "load");
});
