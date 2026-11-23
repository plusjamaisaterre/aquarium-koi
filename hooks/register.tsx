import type { Register, ThemeMessageRule, ThemeSetArgs, ThemeStyle } from 'claude-code'

import { makeColors } from './make-colors.js'
import { SCENE } from './scene'

// A sunlit reef aquarium, made for dark mode: deep lagoon blues for the panels,
// koi orange, lagoon teal and gold for the accents.
const { theme, problems } = makeColors({
  label: 'Aquarium Koi',
  only: 'dark',
  roles: { accent: '#ff8a3d', danger: '#ff4d6d', success: '#3ee0a0', warning: '#ffc93d', pro: '#b98cff' },
  dark: {
    gray: {
      anchors: {
        'surface-0': '#041f33',
        'surface-1': '#06293f',
        'surface-2': '#08314a',
        'surface-3': '#09344d',
        'text-primary': '#effdff',
        'text-secondary': '#c2e9f2',
        'text-muted': '#94c8d6',
      },
    },
    git: { added: '#3ee0a0', removed: '#ff5f7a', modified: '#ffc93d', merged: '#b98cff' },
  },
})

// A pixel frame with stepped corners, a 3-point "pixel" like the scene's art,
// and a little glint of light in the top-left corner.
const FRAME_OUTER = 'M6 0H24V3H27V6H30V24H27V27H24V30H6V27H3V24H0V6H3V3H6Z'
const FRAME_INNER = 'M6 3H24V6H27V24H24V27H6V24H3V6H6Z'
const GLINT = 'M6 6H12V9H9V12H6Z'

type Color = NonNullable<ThemeMessageRule['color']>

const pixelBubble = (fill: Color, border: Color, text: Color, glint: Color): ThemeMessageRule => ({
  color: text,
  backgroundColor: fill,
  paddingX: 16,
  paddingY: 12,
  shadow: { x: 3, y: 3, blur: 0, color: '#021526aa' },
  fill: {
    vector: {
      viewBox: 30,
      slice: 12,
      paths: [
        { d: FRAME_OUTER, color: border },
        { d: FRAME_INNER, color: fill },
        { d: GLINT, color: glint },
      ],
    },
  },
})

const STYLE: ThemeStyle = {
  Heading: { color: '#ffd25e', fontFamily: ['mono'], fontWeight: 'bold' },
  // the person's messages: koi orange, lagoon teal, gold, coral pink
  UserMessage: [
    pixelBubble('#ff9255', '#8a2e10', '#2a1005', '#ffe2c8'),
    pixelBubble('#46dccd', '#0d5c62', '#04292a', '#e0fffb'),
    pixelBubble('#ffd25e', '#8a5a0a', '#2e2104', '#fff6d0'),
    pixelBubble('#ff8fbf', '#8a2350', '#2c0716', '#ffe4f0'),
  ],
  // Claude's replies: a deep-water glass panel with a turquoise pixel frame
  AssistantMessage: pixelBubble('#05273d', '#4fd0ee', '#effdff', '#9feaff'),
  ToolUse: { color: '#c2eef7', backgroundColor: '#04223aee', radius: 3, borderColor: '#1f7fa8', borderWidth: 1, paddingX: 8 },
}

const BASE: ThemeSetArgs = {
  colors: theme,
  backdrop: { scene: 'aquarium', glass: { blur: 8, tint: '#05243c', opacity: 0.5 } },
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const unpainted = problems.find(line => line.startsWith("Desktop won't paint"))

    if (unpainted !== undefined) {
      $.ui.toast(unpainted)
    }

    // An older build may refuse `style`: set the look again without it.
    for (const look of [{ ...BASE, style: STYLE }, BASE]) {
      try {
        const set = await $.theme.set(look)

        if (!set.isDrawn) {
          $.ui.status(set.reason)
        }
        break
      } catch (error) {
        $.ui.log(String(error))
      }
    }

    return next(e)
  })

  // The scene never changes once drawn, so nothing restarts: clicks make a ripple
  // in the water shader, and feeding time is part of the scene itself.
  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    if (e.surface !== 'desktop' && e.surface !== 'mobile') {
      return next(e)
    }
    if (e.props.scene !== 'aquarium') {
      return next(e)
    }

    const { Shader, Svg } = $.ui.resolve(e)

    return (
      <Shader module="./water.ts">
        <Svg source={SCENE} alt="A sunlit pixel-art aquarium with koi, sea turtles, a torii gate, stone lanterns and a coral reef" isInteractive />
      </Shader>
    )
  })
}
