const MAX_CELLS = 60000;
const BASE_DT = 1 / 60;
const MAX_INPUT_DT = .1;
const SPEED = 74;
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const dimension = (value, fallback) => Number.isFinite(value) && value > 0 ? clamp(value, 1, 1e6) : fallback;

export const WAVE_LIMITS = Object.freeze({maxCells: MAX_CELLS, maxInputDt: MAX_INPUT_DT, maxStepsPerCall: 64, speed: SPEED});

/** A signed, linear water-height field. Coordinates are on the lake plane. */
export class WaveField {
  constructor(options = {}) {
    this.resize(options);
  }

  resize({width = 1280, depth = 1018, cellSize = 5} = {}) {
    this.width = dimension(width, 1280);
    this.depth = dimension(depth, 1018);
    const spacing = Number.isFinite(cellSize) && cellSize > 0 ? Math.max(.5, cellSize) : 5;
    let cols = Math.max(3, Math.ceil(this.width / spacing) + 1);
    let rows = Math.max(3, Math.ceil(this.depth / spacing) + 1);
    if (cols * rows > MAX_CELLS) {
      cols = clamp(Math.floor(Math.sqrt(MAX_CELLS * this.width / this.depth)), 3, Math.floor(MAX_CELLS / 3));
      rows = Math.max(3, Math.floor(MAX_CELLS / cols));
    }
    this.cols = cols;
    this.rows = rows;
    this.cellX = this.width / (cols - 1);
    this.cellZ = this.depth / (rows - 1);
    this.speed = SPEED;
    // The conservative Courant bound also covers unusually small viewports.
    this.fixedDt = Math.min(BASE_DT, .68 / (SPEED * Math.hypot(1 / this.cellX, 1 / this.cellZ)));
    this.lambdaX = (SPEED * this.fixedDt / this.cellX) ** 2;
    this.lambdaZ = (SPEED * this.fixedDt / this.cellZ) ** 2;
    this.current = new Float32Array(cols * rows);
    this.previous = new Float32Array(cols * rows);
    this.next = new Float32Array(cols * rows);
    this.damping = new Float32Array(cols * rows);
    const edgeWidth = Math.max(2, Math.min(14, Math.min(cols - 1, rows - 1) * .12));
    for (let z = 0; z < rows; z++) {
      for (let x = 0; x < cols; x++) {
        const edge = Math.min(x, z, cols - 1 - x, rows - 1 - z);
        const sponge = Math.max(0, 1 - edge / edgeWidth);
        // Smoothly increase velocity damping before the fixed zero boundary.
        this.damping[z * cols + x] = (.65 + 8 * sponge ** 2) * this.fixedDt;
      }
    }
    this.accumulator = 0;
    this.simulatedTime = 0;
    return this;
  }

  disturb(x, z, strength = .8, radius = 2) {
    if (![x, z, strength, radius].every(Number.isFinite) || radius <= 0) return;
    const amplitude = clamp(strength, -8, 8);
    if (!amplitude) return;
    x = clamp(x, 0, this.width);
    z = clamp(z, 0, this.depth);
    const sigma = clamp(Math.max(radius, Math.min(this.cellX, this.cellZ) * .65), .25, Math.max(this.width, this.depth));
    const reach = sigma * 3;
    const x0 = Math.max(1, Math.floor((x - reach) / this.cellX));
    const x1 = Math.min(this.cols - 2, Math.ceil((x + reach) / this.cellX));
    const z0 = Math.max(1, Math.floor((z - reach) / this.cellZ));
    const z1 = Math.min(this.rows - 2, Math.ceil((z + reach) / this.cellZ));
    const inverseSigma = 1 / (2 * sigma * sigma);
    for (let j = z0; j <= z1; j++) {
      const dz = j * this.cellZ - z;
      for (let i = x0; i <= x1; i++) {
        const dx = i * this.cellX - x;
        const value = amplitude * Math.exp(-(dx * dx + dz * dz) * inverseSigma);
        const index = j * this.cols + i;
        this.current[index] += value;
        // A mostly displaced surface with a small initial downward/upward push.
        this.previous[index] += value * .8;
      }
    }
  }

  step(dt) {
    if (!Number.isFinite(dt) || dt <= 0) return 0;
    this.accumulator += Math.min(MAX_INPUT_DT, dt);
    let steps = 0;
    while (this.accumulator + 1e-10 >= this.fixedDt && steps < WAVE_LIMITS.maxStepsPerCall) {
      this.advance();
      this.accumulator -= this.fixedDt;
      this.simulatedTime += this.fixedDt;
      steps++;
    }
    if (this.accumulator < 0) this.accumulator = 0;
    if (steps === WAVE_LIMITS.maxStepsPerCall) this.accumulator %= this.fixedDt;
    return steps;
  }

  advance() {
    const {cols, rows, current: u, previous: p, next: n, damping, lambdaX: lx, lambdaZ: lz} = this;
    // A nine-point correction reduces the small-radius diamond bias of a
    // five-point stencil. All terms remain linear, including the sponge.
    // Use the smaller directional weight so even very thin viewports retain
    // nonnegative neighbour weights and the conservative stability bound.
    const cross = Math.min(lx, lz) / 6;
    for (let z = 1; z < rows - 1; z++) {
      let index = z * cols + 1;
      for (let x = 1; x < cols - 1; x++, index++) {
        const center = u[index];
        const horizontal = u[index - 1] + u[index + 1];
        const vertical = u[index - cols] + u[index + cols];
        const diagonal = u[index - cols - 1] + u[index - cols + 1] + u[index + cols - 1] + u[index + cols + 1];
        const laplacian = lx * (horizontal - 2 * center) + lz * (vertical - 2 * center)
          + cross * (diagonal - 2 * horizontal - 2 * vertical + 4 * center);
        const damp = damping[index];
        n[index] = (2 * center - (1 - damp) * p[index] + laplacian) / (1 + damp);
      }
    }
    this.previous = u;
    this.current = n;
    this.next = p;
  }

  sample(x, z) {
    if (!Number.isFinite(x) || !Number.isFinite(z)) return 0;
    const gx = clamp(x / this.cellX, 0, this.cols - 1);
    const gz = clamp(z / this.cellZ, 0, this.rows - 1);
    const ix = Math.min(this.cols - 2, Math.floor(gx));
    const iz = Math.min(this.rows - 2, Math.floor(gz));
    const tx = gx - ix, tz = gz - iz;
    const index = iz * this.cols + ix, u = this.current;
    const a = u[index] * (1 - tx) + u[index + 1] * tx;
    const b = u[index + this.cols] * (1 - tx) + u[index + this.cols + 1] * tx;
    return a * (1 - tz) + b * tz;
  }

  get energy() {
    let sum = 0;
    const {current: u, previous: p, cols, rows, fixedDt: dt, cellX: dx, cellZ: dz} = this;
    for (let z = 1; z < rows - 1; z++) {
      for (let x = 1; x < cols - 1; x++) {
        const i = z * cols + x;
        const velocity = (u[i] - p[i]) / dt;
        const gx = (u[i + 1] - u[i]) / dx;
        const gz = (u[i + cols] - u[i]) / dz;
        sum += velocity * velocity + SPEED * SPEED * (gx * gx + gz * gz);
      }
    }
    return sum / (cols * rows);
  }
}
