# Koi Site Design Analysis

## Overview

The referenced design is a cinematic website hero built from a small number of carefully layered elements. Its premium feeling comes primarily from the animated koi, while the typography and interface remain deliberately restrained.

The koi is unlikely to be a flat image moved with CSS alone. Across the supplied frames, its body bends, its fins move, and its perspective changes as it turns toward the camera. That requires either a rigged 3D model or a pre-rendered animation created from one.

For a short, controlled hero sequence, the most practical implementation is a pre-rendered transparent video or image sequence placed over HTML typography. A real-time Three.js model is more appropriate when the fish must respond interactively to scrolling or pointer movement.

## Composition and Layering

The hero can be understood as the following stack:

```text
Navigation and small edge labels
        ↓
Oversized “CREATE DAILY” typography
        ↓
Animated koi
        ↓
Animated contact shadow
        ↓
Solid red background
```

The fish passes in front of the headline through ordinary depth layering. Its changing position, scale, orientation, and shadow create the impression of moving through three-dimensional space.

## Why the Motion Feels Three-Dimensional

- The koi follows a curved swimming path instead of moving in a straight line.
- Its scale increases as it approaches the viewer.
- It bends and changes perspective during the camera-facing turn.
- Its fins and tail provide secondary motion.
- The contact shadow changes position, scale, blur, and opacity independently.
- Most of the surrounding interface stays still, keeping attention on the fish.

## Visual System

The design uses a deliberately limited visual language:

- A saturated red background
- Oversized white grotesk typography
- Small technical or editorial annotations
- Minimal navigation and interface furniture
- A highly detailed red-and-white koi as the primary visual

This contrast between a simple graphic environment and a complex moving object makes the hero feel more expensive than its underlying layout actually is.

## Likely Implementation

A simplified structure might look like this:

```html
<section class="hero">
  <h1>CREATE<br>DAILY</h1>
  <div class="fish-shadow"></div>
  <video class="koi" autoplay muted loop playsinline>
    <!-- Transparent animation sources -->
  </video>
</section>
```

GSAP or a similar animation library can control the overall path, scale, and orientation:

```js
gsap.timeline({ repeat: -1 })
  .fromTo(
    ".koi",
    { xPercent: 55, yPercent: -20, scale: 0.75, rotate: -25 },
    { xPercent: -5, yPercent: 10, scale: 1.15, rotate: 5, duration: 5 }
  )
  .to(".koi", {
    xPercent: -45,
    yPercent: 15,
    scale: 1.35,
    rotate: 18,
    duration: 5
  });
```

The detailed swimming deformation should remain inside the rendered video or rigged 3D animation. Browser animation should control only its broader movement through the composition.

Possible delivery formats include:

- Transparent WebM with an HEVC-alpha fallback
- A transparent PNG or WebP image sequence
- A rigged `.glb` model rendered with Three.js

## Adapting the Concept to a Japanese Tea Kettle

The same design principle can be applied to a Japanese tea scene: one highly expressive object, restrained typography, and atmospheric motion.

A **tetsubin** is a traditional cast-iron kettle used primarily to heat water. A **kyūsu** is the teapot normally used to brew and pour tea. A tetsubin provides the stronger sculptural centerpiece, while a nearby cup can imply the complete tea ritual.

### Suggested Art Direction

- Deep tea-black or warm parchment background
- Oversized headline such as `STEEP / SLOWLY`
- A beautifully lit tetsubin overlapping the headline
- Steam moving both behind and in front of the kettle
- A soft contact shadow beneath it
- Small Japanese-inspired editorial labels near the edges
- One restrained accent color: matcha green, persimmon red, or antique gold

The layers could be arranged as follows:

```text
Navigation and small annotations
        ↓
Large editorial headline
        ↓
Rear steam
        ↓
Tetsubin
        ↓
Foreground steam
        ↓
Contact shadow and surface
        ↓
Background
```

Splitting the steam into foreground and background layers allows wisps to pass both behind and in front of the kettle, creating depth.

## Suggested Ten-Second Motion Loop

1. **0–2 seconds:** The kettle remains nearly still while a faint wisp emerges from the spout.
2. **2–5 seconds:** The steam becomes denser and curls across part of the headline. Light moves slowly across the iron texture.
3. **5–7 seconds:** The kettle rotates or advances by only a few degrees. The handle responds with subtle secondary movement.
4. **7–9 seconds:** A stronger plume blooms toward the camera. A small highlight or condensation detail appears near the lid.
5. **9–10 seconds:** The steam dissipates and the composition returns seamlessly to its opening state.

The kettle should feel heavy. Large floating movements would weaken the concept. Most of the life should come from the steam, lighting, shadow, and minute vibration.

## Recommended Production Workflow

1. Create or obtain a high-quality 3D tetsubin model.
2. Texture it with dark cast iron, subtle oxidation, and warm highlights.
3. Animate the kettle, lid, lighting, and steam in Blender.
4. Export separate transparent loops for the kettle, rear steam, and foreground steam.
5. Place the rendered assets over responsive HTML typography.
6. Use GSAP to coordinate entrances, scale changes, and optional scroll behavior.

Use Three.js instead when the kettle needs to rotate with the pointer, react to scrolling, or respond to user input in real time.

## Example Creative Direction

```text
Headline:        STEEP
                 SLOWLY

Small labels:    cast iron / spring water / 80°C
Japanese text:   静けさの一服
CTA:             ENTER THE RITUAL
```

Suggested palette:

```text
Charcoal:       #151411
Warm paper:     #E8DDC5
Matcha:         #66704A
Persimmon:      #C94E31
Antique gold:   #A68A58
```

## Image-Generation Starting Prompt

> A museum-quality Japanese cast-iron tetsubin tea kettle, three-quarter view, sculptural black iron surface with delicate traditional texture, subtle bronze highlights, warm directional studio lighting, graceful white steam curling from the spout, dark minimal background, refined Japanese editorial art direction, premium product photography, realistic proportions, dramatic soft shadow, isolated central composition, no text, no hands, no additional objects.

Generate the kettle without typography. The headline, annotations, navigation, and call to action should be constructed in HTML so they remain sharp, accessible, and responsive.

## Central Creative Principle

The koi communicates energy through movement. The kettle should communicate calm through restraint. In the adapted design, steam becomes the living element that carries the composition.

## Reference

- [Original X article/post](https://x.com/0xkenny1st/status/2091554298920329465)
