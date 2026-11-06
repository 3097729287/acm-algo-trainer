# Open Water rain optics

Source: https://github.com/Leonxlnx/open-water/tree/3d1adaa1154f98e639a6c6e0f7c514bbeb0496b8 (MIT).
The original rain source, README and license are retained verbatim and hashed in `UPSTREAM.json`.

The adapter takes the existing `STREAK_VS` and `STREAK_FS` from this source. It preserves its Marshall–Palmer drop distribution, Atlas terminal velocities, camera-facing optical footprint, exposure coverage, soft transverse/longitudinal profiles and sky-light scattering. It does not use a sphere, ellipsoid or opaque drop material.

Host changes are limited to a Three.js instanced draw, Y/Z coordinate conversion, the lake's existing cubemap rather than an equirectangular sky, and standard linear-to-sRGB output encoding. Exposure and visibility gain are calibrated for the existing blue-gray lake and an ordinary 8-bit cubemap rather than the original HDR post-processing pipeline. The physical-width antialiasing footprint is 1.8 pixels for clarity.

Instead of the upstream wrapped volume, vertex positions come from the actual collision-owning drop objects. Each of those uses the upstream terminal-speed formula. Its surface crossing triggers exactly one CheapWater ripple at the same location. The upstream independent splash/ripple fields and audio are not imported. This retains the approved shallow lake camera and long-lived expanding rings without decoupling the visible rain from its impact.

The lake shaders, ripple image and reflection images remain the existing MIT CheapWater source; this is a replacement of the rain-rendering system, not a retuned solid-bead material. Both render passes share the same camera. No new rain or ripple shader was authored for this integration.
