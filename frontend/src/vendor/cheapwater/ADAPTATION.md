# CheapWater integration

Upstream: https://github.com/mqnc/cheapwater/tree/f892228d701522fb26d8cdbcf0b360767705aedf (MIT).
`UPSTREAM.json` hashes the original HTML, textures, README and license. `scene.js` extracts the original normal-map shader, two-pass sprite blending, falling drops and collision-triggered ripples into a disposable scene factory. There is no separately randomized ripple layer.

Host adaptations: fixed shallow perspective camera, soft blue-gray palette/fog, offline texture URLs, exactly one original ripple per actual collision, 10.8 second opacity lifetimes, resource disposal and pause/resize lifecycle. A larger plane and weaker distance fog extend the lake toward the upper quarter of the picture. The moving demonstration ball, keyboard controls and OrbitControls are omitted. The upstream water shader and sprite texture retain their original calculations. Both normal and color passes always use the same camera and drawing-buffer resolution.

The solid sphere/ellipsoid drops are removed. Rain now uses the pinned MIT Open Water photographic shaders, instanced for the same actual drop positions; its terminal velocities determine the drop motion. Near, middle and distant particles still trigger only their own collision ripple. See `../open-water-rain/ADAPTATION.md`. The original independently randomized splash generators are not used.

Upstream environmental cubemap attribution: https://hdri-haven.com/hdri/winter-european-meadow (as credited by the author). It supplies reflections only; the application renders a plain blue-gray sky. Three.js 0.186.0 is pinned to the version used by this upstream commit (MIT).
