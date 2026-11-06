# CheapWater integration

Upstream: https://github.com/mqnc/cheapwater/tree/f892228d701522fb26d8cdbcf0b360767705aedf (MIT).
`UPSTREAM.json` hashes the original HTML, textures, README and license. `scene.js` extracts the original normal-map shader, two-pass sprite blending, falling drops and collision-triggered ripples into a disposable scene factory. There is no separately randomized ripple layer.

Host adaptations: fixed shallow perspective camera, soft blue-gray palette/fog, offline texture URLs, visible elongated raindrop meshes, 96 drops/second across near and distant water, three original ring sprites per actual collision, 4.2–7.2 second opacity lifetimes, resource disposal and pause/resize lifecycle. A larger plane and weaker distance fog extend the lake toward the upper quarter of the picture; one original normal-map overlay keeps distant water visible without a moving camera. The moving demonstration ball, keyboard controls and OrbitControls are omitted. The upstream water shader and sprite texture retain their original calculations. Both normal and color passes always use the same camera and drawing-buffer resolution.

Upstream environmental cubemap attribution: https://hdri-haven.com/hdri/winter-european-meadow (as credited by the author). It supplies reflections only; the application renders a plain blue-gray sky. Three.js 0.186.0 is pinned to the version used by this upstream commit (MIT).
