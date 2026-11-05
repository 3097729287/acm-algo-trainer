// Coordinates, velocities and gravity use the illustration's SVG units.
const cross = (a, b) => a[0] * b[1] - a[1] * b[0];
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

export function fractureCells(bounds, seeds) {
 const {x, y, width, height} = bounds;
 return seeds.map(([sx, sy], index) => {
  let polygon = [[x, y], [x + width, y], [x + width, y + height], [x, y + height]];
  for (const [other, [tx, ty]] of seeds.entries()) {
   if (other === index) continue;
   const nx = tx - sx, ny = ty - sy, boundary = (tx * tx + ty * ty - sx * sx - sy * sy) / 2, next = [];
   for (let i = 0; i < polygon.length; i++) {
    const a = polygon[i], b = polygon[(i + 1) % polygon.length];
    const da = a[0] * nx + a[1] * ny - boundary, db = b[0] * nx + b[1] * ny - boundary;
    if (da <= 0) next.push(a);
    if (da < 0 && db > 0 || da > 0 && db < 0) {
     const fraction = da / (da - db);
     next.push([a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction]);
    }
   }
   polygon = next;
  }
  return {polygon, x: sx, y: sy};
 });
}

// Intersect material outlines with each convex cell. Empty space (including
// the cup handle's hole) contributes neither mass nor floor contact points.
export function clipFracturePolygon(outline, cell) {
 let result = outline;
 for (let edge = 0; edge < cell.length && result.length; edge++) {
  const a = cell[edge], b = cell[(edge + 1) % cell.length], direction = [b[0] - a[0], b[1] - a[1]], next = [];
  for (let i = 0; i < result.length; i++) {
   const p = result[i], q = result[(i + 1) % result.length];
   const dp = cross(direction, [p[0] - a[0], p[1] - a[1]]), dq = cross(direction, [q[0] - a[0], q[1] - a[1]]);
   if (dp >= 0) next.push(p);
   if (dp < 0 && dq > 0 || dp > 0 && dq < 0) {
    const t = dp / (dp - dq);
    next.push([p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t]);
   }
  }
  result = next;
 }
 return result;
}

function hull(points) {
 const sorted = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
 const half = points => {
  const result = [];
  for (const point of points) {
   while (result.length > 1) {
    const a = result.at(-2), b = result.at(-1);
    if (cross([b[0] - a[0], b[1] - a[1]], [point[0] - b[0], point[1] - b[1]]) > 1e-8) break;
    result.pop();
   }
   result.push(point);
  }
  return result.slice(0, -1);
 };
 return [...half(sorted), ...half(sorted.reverse())];
}

export function fractureGeometry(polygons) {
 let area = 0, mx = 0, my = 0, moment = 0;
 for (const polygon of polygons) {
  let signed = 0, cx = 0, cy = 0, inertia = 0;
  for (let i = 0; i < polygon.length; i++) {
   const a = polygon[i], b = polygon[(i + 1) % polygon.length], weight = cross(a, b);
   signed += weight; cx += (a[0] + b[0]) * weight; cy += (a[1] + b[1]) * weight;
   inertia += weight * (a[0] ** 2 + a[0] * b[0] + b[0] ** 2 + a[1] ** 2 + a[1] * b[1] + b[1] ** 2);
  }
  if (Math.abs(signed) < 1e-6) continue;
  const sign = Math.sign(signed);
  area += Math.abs(signed) / 2; mx += sign * cx / 6; my += sign * cy / 6; moment += sign * inertia / 12;
 }
 if (area < .08) return null;
 const cx = mx / area, cy = my / area, points = hull(polygons.flat()).map(([x, y]) => [x - cx, y - cy]);
 return {area, cx, cy, points, radius: Math.max(...points.map(p => Math.hypot(...p))), inertia: Math.max(.1, moment / area - cx * cx - cy * cy)};
}

export function fractureKineticEnergy(bodies) {
 return bodies.reduce((sum, b) => sum + .5 * (b.mass * (b.vx ** 2 + b.vy ** 2) + b.inertia * b.spin ** 2), 0);
}

export function createFractureBodies(geometries, {material, impact, impactSpeed = 260, random = Math.random}) {
 const glass = material === 'glass';
 const bodies = geometries.map((geometry, index) => {
  const {area, cx, cy, radius} = geometry, mass = area * (glass ? .45 : 1);
  // Low impulse pieces collapse where they were; a smaller share absorbs the
  // outward impulse. The common energy budget below prevents extra energy
  // from appearing merely because the fracture contains more small shards.
  const local = index % 5 !== 1 && index % 5 !== 4;
  const size = clamp(Math.sqrt(100 / area), .6, 1.8), strength = local ? .025 + random() * .045 : .48 + random() * .42;
  const dx = cx - impact.x, dy = cy - impact.y;
  let angle = Math.atan2(dy, dx) + (random() - .5) * .5;
  if (!glass) angle = -Math.PI / 2 + clamp(dx / 30, -1, 1) * 1.05 + (random() - .5) * .3;
  const speed = impactSpeed * strength * size;
  return {...geometry, x: cx, y: cy, angle: 0, mass, inertia: mass * geometry.inertia,
   // The upper wall retains its downward momentum as the base hits. Stopping
   // these bodies here leaves a recognisable cup standing on the floor.
   vx: Math.cos(angle) * speed, vy: local ? (glass ? 10 : impactSpeed*clamp(.25+(impact.y-cy)/55,.25,.85)) : Math.sin(angle) * speed,
   spin: (random() - .5) * speed / Math.max(3, radius) * (local ? .6 : 1.5),
   mode: local ? 'collapse' : 'eject', asleep: false, quiet: 0, contacts: 0};
 });
 const energy = fractureKineticEnergy(bodies), mass = bodies.reduce((sum, b) => sum + b.mass, 0);
 const budget = .5 * mass * impactSpeed ** 2 * (glass ? .24 : .32);
 const scale = Math.min(1, Math.sqrt(budget / Math.max(energy, 1)));
 for (const b of bodies) { b.vx *= scale; b.vy *= scale; b.spin *= scale; }
 return bodies;
}

export function fractureVertices(body) {
 const c = Math.cos(body.angle), s = Math.sin(body.angle);
 return body.points.map(([x, y]) => [body.x + x * c - y * s, body.y + x * s + y * c]);
}

function support(vertices, nx, ny) {
 const distances = vertices.map(([x, y]) => x * nx + y * ny), max = Math.max(...distances);
 const edge = vertices.filter((_, i) => distances[i] > max - .15);
 return [edge.reduce((v, p) => v + p[0], 0) / edge.length, edge.reduce((v, p) => v + p[1], 0) / edge.length];
}

function overlap(a, b, va, vb) {
 let depth = Infinity, nx = 0, ny = 0;
 for (const polygon of [va, vb]) for (let i = 0; i < polygon.length; i++) {
  const p = polygon[i], q = polygon[(i + 1) % polygon.length], length = Math.hypot(q[0] - p[0], q[1] - p[1]);
  if (length < 1e-6) continue;
  const x = (p[1] - q[1]) / length, y = (q[0] - p[0]) / length;
  const pa = va.map(p => p[0] * x + p[1] * y), pb = vb.map(p => p[0] * x + p[1] * y);
  const d = Math.min(Math.max(...pa), Math.max(...pb)) - Math.max(Math.min(...pa), Math.min(...pb));
  if (d <= .025) return null;
  if (d < depth) { depth = d; nx = x; ny = y; }
 }
 if ((b.x - a.x) * nx + (b.y - a.y) * ny < 0) { nx = -nx; ny = -ny; }
 const pa = support(va, nx, ny), pb = support(vb, -nx, -ny);
 return {depth, nx, ny, x: (pa[0] + pb[0]) / 2, y: (pa[1] + pb[1]) / 2};
}

function collide(a, b, contact, restitution, friction) {
 const {nx, ny, x, y} = contact, ax = x - a.x, ay = y - a.y, bx = b ? x - b.x : 0, by = b ? y - b.y : 0;
 const rvx = (b ? b.vx - b.spin * by : 0) - a.vx + a.spin * ay;
 const rvy = (b ? b.vy + b.spin * bx : 0) - a.vy - a.spin * ax;
 const closing = rvx * nx + rvy * ny;
 if (closing >= 0) return;
 if (a.asleep && closing < -20) { a.asleep = false; a.quiet = 0; }
 if (b?.asleep && closing < -20) { b.asleep = false; b.quiet = 0; }
 const ma = a.asleep ? 0 : 1 / a.mass, mb = !b || b.asleep ? 0 : 1 / b.mass;
 const ia = a.asleep ? 0 : 1 / a.inertia, ib = !b || b.asleep ? 0 : 1 / b.inertia;
 const ca = ax * ny - ay * nx, cb = bx * ny - by * nx;
 const denominator = ma + mb + ca * ca * ia + cb * cb * ib;
 if (!denominator) return;
 const normal = -(1 + (closing < -45 ? restitution : 0)) * closing / denominator;
 const apply = (jx, jy) => {
  a.vx -= jx * ma; a.vy -= jy * ma; a.spin -= (ax * jy - ay * jx) * ia;
  if (b) { b.vx += jx * mb; b.vy += jy * mb; b.spin += (bx * jy - by * jx) * ib; }
 };
 apply(nx * normal, ny * normal);
 const tx = -ny, ty = nx, ta = ax * ty - ay * tx, tb = bx * ty - by * tx;
 const tangentVelocity = ((b ? b.vx - b.spin * by : 0) - a.vx + a.spin * ay) * tx + ((b ? b.vy + b.spin * bx : 0) - a.vy - a.spin * ax) * ty;
 const tangent = clamp(-tangentVelocity / (ma + mb + ta * ta * ia + tb * tb * ib), -friction * normal, friction * normal);
 apply(tx * tangent, ty * tangent);
}

// The caller uses a fixed 1/240 s timestep. Contact impulses include rotational
// inertia, restitution and Coulomb friction; sleep only follows quiet contact.
export function stepFracture(bodies, dt, {floor, gravity = 1800, material}) {
 const glass = material === 'glass', restitution = glass ? .24 : .14, friction = glass ? .48 : .68;
 for (const b of bodies) {
  b.touching = false;
  if (b.asleep) continue;
  b.x += b.vx * dt; b.y += b.vy * dt + .5 * gravity * dt * dt; b.vy += gravity * dt; b.angle += b.spin * dt;
  const drag = Math.exp(-(glass ? .65 : .25) * dt); b.vx *= drag; b.spin *= drag;
 }
 for (let iteration = 0; iteration < 6; iteration++) {
  for (let i = 0; i < bodies.length; i++) for (let j = i + 1; j < bodies.length; j++) {
   const a = bodies[i], b = bodies[j];
   if (a.asleep && b.asleep || Math.hypot(a.x - b.x, a.y - b.y) > a.radius + b.radius) continue;
   const contact = overlap(a, b, fractureVertices(a), fractureVertices(b));
   if (!contact) continue;
   collide(a, b, contact, Math.min(.12, restitution), friction);
   const ma = a.asleep ? 0 : 1 / a.mass, mb = b.asleep ? 0 : 1 / b.mass, correction = Math.max(0, contact.depth - .035) * .8 / (ma + mb || 1);
   a.x -= contact.nx * correction * ma; a.y -= contact.ny * correction * ma;
   b.x += contact.nx * correction * mb; b.y += contact.ny * correction * mb;
   a.touching = b.touching = true;
  }
  for (const b of bodies) {
   if (b.asleep) continue;
   const vertices = fractureVertices(b), bottom = support(vertices, 0, 1);
   bottom[1] = Math.max(...vertices.map(p => p[1]));
   if (bottom[1] < floor - .04) continue;
   b.y -= Math.max(0, bottom[1] - floor);
   collide(b, null, {nx: 0, ny: 1, x: bottom[0], y: floor}, restitution, friction);
   b.touching = true; b.contacts++;
  }
 }
 for (const b of bodies) {
  if (b.asleep) continue;
  // Irregular edges lose rotation through repeated small contact impacts.
  if (b.touching) b.spin *= Math.exp(-6 * dt);
  // Adjacent polygons retain a tiny solver gap; it must not restart the sleep
  // timer between otherwise quiet support contacts on successive substeps.
  b.contactAge = b.touching ? 0 : (b.contactAge ?? 1) + dt;
  b.quiet = b.contactAge < .025 && Math.hypot(b.vx, b.vy) < 18 && Math.abs(b.spin) < 1 ? b.quiet + dt : Math.max(0,b.quiet-dt*2);
  if (b.quiet > .075) { b.asleep = true; b.vx = b.vy = b.spin = 0; }
 }
}
