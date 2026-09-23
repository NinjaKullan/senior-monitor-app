# Backdrop prompts

Each backdrop was painted once by `node paint.mjs <name> [reference.png]`, which sends the
**style** block, a blank line, then the named block below, exactly as written here.
A reference image, where listed, is sent with the prompt to keep one world.
Render never calls Gemini; it only reads the PNGs in this folder.

## style
```
Paper-cutout illustration, like layered hand-cut construction paper photographed flat from above: flat shapes with slightly torn, uneven edges, a faint paper grain, and a soft pale grey-green drop shadow under each cut piece. Use only this palette: warm paper #F7F1E8, soft ink #403C36, Kettle green #297A5C, pale grey-green #C9D3C6, warm yellow #E8C77A (only for lamp light, window light and the morning sun), deep blue-green #1F3B3B (only for night sky). No pure black, no pure white, no red, no orange, no neon, no glossy or 3D shading. Tall vertical 9:16 image. Absolutely no text, letters, numbers, signs, logos or writing anywhere. No people, no hands, no faces, no bodies, no silhouettes, no animals. No phones, no screens, no devices. Calm, cozy, warm, lived-in mood.
```

## apartment-night
```
Inside a small, cozy city apartment at night, seen straight on. Upper middle: a large window showing a deep blue-green night sky, a crescent moon, a few paper stars, and the warm yellow lit windows of other city buildings. Soft curtains at the window edges. Lower third: a simple table top in pale grey-green paper spanning the width. On the left side of the table a mug and a small potted plant; a small table lamp casts a warm yellow pool of light. The right half of the table top is completely clear and empty. The band from 12% to 32% of the image height, measured from the top, is calm plain wall or sky with no detail. It should feel warm and lived-in, never empty or lonely.
```

## apartment-dawn
Reference: `apartment-night.png`
```
The same apartment interior as the reference image: same window, curtains, table, mug, plant and lamp, same framing. Now it is early morning: the window shows a soft pale morning sky with the warm yellow sun low over the city buildings, and the lamp is off. The right half of the table top is still completely clear and empty. The band from 12% to 32% of the image height is calm and plain.
```

## mom-house
Reference: `apartment-night.png` (style only)
```
Match the paper style and palette of the reference image, but show a different place. A small single-storey house on a gentle green hill at dawn, seen from the front, filling the middle of the frame. Cream walls, a Kettle-green roof, a chimney, a dark ink door, and one square kitchen window on the right half of the front wall. The kitchen window is unlit, plain pale grey-green. Soft paper sky with the warm yellow sun just rising behind the hill on the right, a few paper clouds, two round green trees and a small garden path. The top 30% of the image is plain calm sky.
```

## kitchen
Reference: `mom-house.png`
```
Match the paper style and palette of the reference image. Inside that small house's kitchen in the morning, seen straight on. Upper right: a window glowing with warm yellow morning light. Lower third: a counter in pale grey-green paper across the width, with a small dark stovetop on the right half. On the stove sits one small stovetop kettle in Kettle green #297A5C with a round body, a curved spout pointing to the right and a dark ink handle arching over the top. The kettle has no face and no eyes. A shelf with two cups, and a small plant on the wall. The left half of the counter top is completely clear and empty.
```

## map
Reference: `mom-house.png`
```
Match the paper style and palette of the reference image. A simple paper-cutout picture map seen from directly above, like a map laid on a table. Near the upper right: one small house with a Kettle-green roof, like the reference house. Near the lower left: a small cluster of three taller cream city apartment buildings with rows of small windows. Between them: gentle rolling hills, a winding pale grey-green river, round green trees. No roads or lines connecting the house and the buildings. The top 25% of the image is plain paper with no detail.
```

## kettle
Reference: `../../social/brand/kettle-x-avatar.png` (the brand kettle: shape and green)
```
One stovetop kettle alone in the centre of the image, the same kettle as the reference image: same round dome body, same small knob lid, same tall arched dark ink handle with a wrapped grip, same straight spout angled up to the right with a flared tip, same thin pale base ring. The kettle body and spout are sage green #9FB699 exactly like the reference; this green is the one exception to the palette. Make it a paper cutout: flat cut paper pieces with slightly torn edges, faint paper grain, a soft pale grey-green drop shadow under the kettle. Flat colour, no shine highlight, no gloss. The kettle has no face and no eyes. The background is completely plain flat paper colour #F7F1E8 with nothing else in the image: no table, no stove, no steam, no pattern. The kettle fills about half the image width.
```

### kettle: recoloured after painting
The painted kettle was sage green (about #A1B598). To match Mom's kitchen kettle it was recoloured,
not repainted: only sage pixels are scaled per channel toward Kettle green #297A5C, so the shape and
paper grain are unchanged; the pale base ring, dark handle and knob are untouched.
```
M='between(g(X,Y)-r(X,Y),11,32)*between(r(X,Y),100,190)'
ffmpeg -i kettle-sage.png -vf "format=rgba,geq=r='if($M,r(X,Y)*0.2547,r(X,Y))':g='if($M,g(X,Y)*0.674,g(X,Y))':b='if($M,b(X,Y)*0.605,b(X,Y))':a='alpha(X,Y)'" -map_metadata -1 -fflags +bitexact kettle.png
```
