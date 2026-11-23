// Water over the pixel aquarium: caustic sparkles near the
// surface, a soft light that follows the pointer, and one ripple ring per click.
import {
  clamp, exp, floor, length, max, picture, pointers, scene, shader, sin,
  size, smoothstep, time, vec2, vec3, vec4,
} from 'claude-code/shader'

const water = picture(p => {
  // one art pixel, in points (the 320 by 180 art is sliced to cover)
  const cell = max(size.x / 320, size.y / 180)
  let at = vec2(p.point)
  let ring = 0
  let glow = 0
  for (const q of pointers) {
    const d = vec2(p.point - q.at)
    const r = length(d)
    const fade = clamp(1 - q.age, 0, 1)
    const front = q.age * 240
    const band = exp(-((r - front) * (r - front)) / 260) * fade * q.down
    ring = ring + band
    at = vec2(at + (d / max(r, 1)) * band * cell * 1.5)
    glow = glow + exp(-(r * r) / 9000) * (1 - q.down) * clamp(1 - q.gone, 0, 1)
  }
  const c = scene.sample(at / size)
  // caustic sparkles, snapped to the art grid, strongest near the surface
  const g = vec2(floor(p.point / cell))
  const cz = sin(g.x * 0.31 + time * 0.6) * sin(g.y * 0.43 - time * 0.5) * sin((g.x + g.y) * 0.11 + time * 0.3)
  const top = clamp(p.uv.y * 1.4 - 0.35, 0, 1)
  const sparkle = smoothstep(0.5, 0.9, cz) * top * 0.14
  const add = vec3(0.75, 0.95, 1) * (ring * 0.2 + sparkle + glow * 0.06)
  return vec4(c.rgb + add, 1)
})

export default shader({ fps: 30, passes: [water] })
