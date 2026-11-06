# ElementalFX rain lake

Pinned upstream: https://github.com/iyerav42/elementalfx/tree/278bce20c688a35a6aeb28407e7c6a165a762681 (MIT).
The original license and file-by-file upstream/adapted SHA-256 records are retained.

The original rain shaders and ripple shaders are unchanged. Water is the upstream
fixed-step GPU height/velocity solver, replacing the entire previous CheapWater
normal-sprite composition. The foreground no longer contains an animated tiled
normal map, reverse-subtract blend sequence, reflective cubemap or a mesh per ring.

Documented host extensions:

- Relative imports make the four small packages available offline without a CDN.
- `speed` changes how quickly original fixed simulation steps are consumed; the
  numerical update equation is unchanged. `localCoordinates` sizes a projected
  canvas before the CSS transform, avoiding an oversized or distorted framebuffer.
- `snapshot()` draws a still without advancing the simulation.
- The existing stamp-batching loop can queue 512 impacts instead of 16, preserving
  every ordinary collision between slow water steps and retaining a bounded queue.
- Weather accepts a configurable distant-water boundary/depth range and a frame
  callback. Every collision reaches the ripple target; the original 50% random
  discard in `onSplash` is removed.
- The host supplies only a static theme gradient, CSS perspective, its inverse
  coordinate conversion, lifecycle and low-contrast visual options. No local rain
  or ripple shader, independent random ripple emitter, solid rain geometry, or
  per-ring reflection composition is added.

`rain-lake-stability.mjs` tests an actual upstream rain-particle collision, compares
the transformed DOM point with the impact, measures wave-front growth over six
seconds, and samples rendered brightness during dense impacts. Optional upstream
lightning remains off by default. Pause, reduced motion, theme changes and disposal
are controlled by the same existing background host.
