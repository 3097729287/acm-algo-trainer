const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const angleDelta = (a, b) => Math.atan2(Math.sin(a - b), Math.cos(a - b));
const smooth = (v) => { const t = clamp(v, 0, 1); return t * t * (3 - 2 * t); };

function randomSource(seed) {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ value >>> 15, value | 1);
    value ^= value + Math.imul(value ^ value >>> 7, value | 61);
    return ((value ^ value >>> 14) >>> 0) / 4294967296;
  };
}

/** Three quiet silhouettes below the surface; no markings or facial details. */
export class FishShadows {
  constructor(seed = 33) {
    this.random = randomSource(seed);
    this.width = 1;
    this.depth = 1;
    this.time = 0;
    this.fishes = [];
  }

  resize(width, depth) {
    const oldWidth = this.width, oldDepth = this.depth;
    this.width = Math.max(64, Number.isFinite(width) ? width : 640);
    this.depth = Math.max(64, Number.isFinite(depth) ? depth : 640);
    if (!this.fishes.length) {
      const starts = [[.24, .37, .4], [.66, .62, 3.5], [.81, .20, 2.2]];
      this.fishes = starts.map(([x, z, heading], index) => ({
        x: x * this.width,
        z: z * this.depth,
        heading,
        turn: 0,
        phase: this.random() * Math.PI * 2,
        size: [.96, 1.14, .84][index],
        speedFactor: [.93, .76, 1.04][index],
        targetX: (.15 + this.random() * .7) * this.width,
        targetZ: (.12 + this.random() * .76) * this.depth,
        nextTarget: 40 + this.random() * 55,
        opacity: .08,
        waterDepth: 14,
        length: 50
      }));
      this.fishes[1].phase = 1.25;
    } else {
      for (const fish of this.fishes) {
        fish.x *= this.width / oldWidth;
        fish.z *= this.depth / oldDepth;
        fish.targetX *= this.width / oldWidth;
        fish.targetZ *= this.depth / oldDepth;
      }
    }
    for (const fish of this.fishes) {
      fish.length = clamp(this.width * .066 * fish.size, 38, 95);
    }
    this.step(0, this.time);
  }

  step(dt, time) {
    const elapsed = Number.isFinite(dt) ? clamp(dt, 0, .2) : 0;
    this.time = Number.isFinite(time) ? time : this.time + elapsed;
    const parts = Math.max(1, Math.ceil(elapsed / (1 / 30)));
    const delta = elapsed / parts;
    for (let i = 0; i < parts; i++) {
      for (const fish of this.fishes) {
        if (this.time >= fish.nextTarget) {
          fish.targetX = (.1 + this.random() * .8) * this.width;
          fish.targetZ = (.1 + this.random() * .8) * this.depth;
          fish.nextTarget = this.time + 45 + this.random() * 70;
        }
        const outside = fish.x < -.08 * this.width || fish.x > this.width * 1.08 ||
          fish.z < -.06 * this.depth || fish.z > this.depth * 1.06;
        const targetX = outside ? this.width * .5 : fish.targetX;
        const targetZ = outside ? this.depth * .5 : fish.targetZ;
        const wanted = Math.atan2(targetZ - fish.z, targetX - fish.x) +
          Math.sin(this.time * .032 + fish.phase) * .16;
        const desiredTurn = clamp(angleDelta(wanted, fish.heading) * .1, -.12, .12);
        fish.turn += (desiredTurn - fish.turn) * (1 - Math.exp(-delta * .38));
        fish.heading += fish.turn * delta;
        const speed = clamp(Math.sqrt(this.width / 1280) * 5.2, 2.6, 6.4) *
          fish.speedFactor * (1 + Math.sin(this.time * .045 + fish.phase) * .11);
        fish.x += Math.cos(fish.heading) * speed * delta;
        fish.z += Math.sin(fish.heading) * speed * delta;
      }
    }
    for (const fish of this.fishes) {
      const glimpse = smooth((Math.sin(this.time * .072 + fish.phase) + .38) / 1.15);
      fish.waterDepth = 12 + Math.sin(this.time * .039 + fish.phase) * 6;
      fish.opacity = (.04 + glimpse * .32) * (1 - (fish.waterDepth - 6) * .012);
    }
  }

  draw(ctx, project, time = this.time) {
    const now = Number.isFinite(time) ? time : this.time;
    ctx.save();
    ctx.fillStyle = '#020a0e';
    ctx.filter = this.width < 600 ? 'blur(1.1px)' : 'blur(2.6px)';
    const baseAlpha = ctx.globalAlpha;
    for (const fish of this.fishes) {
      const length = fish.length;
      const forwardX = Math.cos(fish.heading), forwardZ = Math.sin(fish.heading);
      const sway = Math.sin(now * 1.05 + fish.phase) * length * .023;
      const p = (along, side) => {
        const trailing = clamp(-along / length * 2.3, 0, 1);
        const lateral = side + sway * trailing * trailing;
        return project(fish.x + forwardX * along - forwardZ * lateral,
          fish.z + forwardZ * along + forwardX * lateral, fish.waterDepth);
      };
      const move = (along, side) => { const q = p(along, side); ctx.moveTo(q.x, q.y); };
      const line = (along, side) => { const q = p(along, side); ctx.lineTo(q.x, q.y); };
      const curve = (a, b, c, d, e, f) => {
        const q = p(a, b), r = p(c, d), s = p(e, f);
        ctx.bezierCurveTo(q.x, q.y, r.x, r.y, s.x, s.y);
      };

      ctx.globalAlpha = baseAlpha * fish.opacity;
      ctx.beginPath();
      move(length * .45, 0);
      curve(length * .39, length * .10, length * .11, length * .15,
        -length * .13, length * .10);
      curve(-length * .29, length * .07, -length * .35, length * .025,
        -length * .43, length * .018);
      line(-length * .43, -length * .018);
      curve(-length * .35, -length * .025, -length * .29, -length * .07,
        -length * .13, -length * .10);
      curve(length * .11, -length * .15, length * .39, -length * .10,
        length * .45, 0);
      ctx.closePath();
      ctx.fill();

      ctx.globalAlpha = baseAlpha * fish.opacity * .72;
      ctx.beginPath();
      move(-length * .39, length * .02);
      line(-length * .62, length * .115);
      line(-length * .56, 0);
      line(-length * .62, -length * .115);
      line(-length * .39, -length * .02);
      ctx.closePath();
      ctx.fill();

      ctx.globalAlpha = baseAlpha * fish.opacity * .72 * .55;
      for (const sign of [-1, 1]) {
        ctx.beginPath();
        move(length * .12, sign * length * .09);
        curve(0, sign * length * .17, -length * .10, sign * length * .23,
          -length * .13, sign * length * .17);
        line(-length * .08, sign * length * .085);
        ctx.closePath();
        ctx.fill();
      }
    }
    ctx.restore();
  }
}
