# Gemini prompts

`node paint.mjs <name> style-tests/look-reference.png` (run in this folder) sends the
**style** block, a blank line, then the named block, exactly as written here, with the look
reference attached. Output lands in `candidates/` (gitignored). The pick is copied into `assets/`.
The render never calls Gemini.

Phase 3 mockups are the `mock-*` blocks: one quick flat image per painted shot. Phase 4
layer prompts get added below them.

## style
```
Match the attached reference image exactly in world and finish: a small handmade paper diorama standing on a cream paper-covered table, photographed straight on. Flat cut-paper cards standing upright in two or three shallow planes, soft fibrous paper texture, gently irregular cut edges, soft natural light from the upper left, gentle real paper shadows on the table. Simple friendly silhouettes, broad matte areas, minimal detail, calm. Palette only: paper #F7F1E8, soft ink #403C36, Kettle green #297A5C, warm yellow #E8C77A only for sunlight, lamp light and a lit phone screen. No pure black, no pure white, no red, no orange, no neon, no gloss, no plastic, no metal sheen, no lens flare, no strong blur. Landscape 16:9. Absolutely no text, letters, numbers, logos, signs or writing anywhere. No people, no faces, no hands, no bodies, no animals. No medical items. The top 28% of the image is plain calm cream wall with nothing in it.
```

## mock-map
```
A paper map laid on the table as a low flat stage, seen from slightly above. On the left, a small cluster of three cream paper city apartment buildings with rows of small windows. Far off on the right, one small cream paper house with a Kettle-green roof and a kitchen window, like the reference house. Between them rolling green paper hills, a winding pale river and round green paper trees, and a faint dotted paper path from the buildings to the house. A warm yellow paper sun rising behind the house on the right. Plenty of space between the two places.
```

## mock-kitchen
```
Inside the reference house's kitchen in the morning, seen straight on as a paper diorama. A back wall with a window glowing warm yellow morning light on the right. A cream counter across the lower third with a simple ink stovetop on the right. On the stove, one small stovetop kettle in Kettle green with a round body, curved spout to the right and an ink handle arching over the top, three soft cream paper steam wisps rising from the spout. On the left of the counter, lying flat, a phone made of ink paper with a plain warm yellow lit screen and nothing on the screen. A mug and a small potted plant. Busy, warm, lived-in morning.
```

## mock-phones
```
Close on the cream table: two paper phones lying side by side, face up, both with a plain warm yellow lit screen and nothing on the screens. The left phone is ink-coloured with rounded corners and a single small camera dot. The right phone is Kettle green with squarer corners and a small row of camera dots, clearly a different make. A folded cream paper napkin and a small green paper plant at the edge for scale. Tidy, calm, bright.
```

## mock-quiet
```
The same kitchen as the reference, bright late morning, tidy and calm. The green kettle sits on the stove with no steam. On the cream counter, lying flat on the left, an ink paper phone with a plain dark screen. A mug and the small potted plant. Sunlight through the window on the right. Peaceful and lived-in, not empty or lonely.
```

## mock-thumbs
```
Close on the cream counter: an ink paper phone lying flat with a plain warm yellow lit screen, and a small blank cream paper card resting on its screen. Beside the phone, standing upright, a thumbs-up symbol cut from Kettle green paper as a plain rounded sticker shape: a soft rounded fist block with one rounded thumb pointing up, cut off flat at the bottom with no wrist, no arm, no sleeve, no fingernails, no skin tone. It reads as an emoji-style sticker, not a hand. The green kettle out of focus far behind on the stove. Warm morning light.
```

## Phase 4 layers

Each layer is one object painted flat on solid magenta, then keyed to a transparent PNG by
`blender -b -P blender/cutout.py -- <in> <out>`. Blender stands the cutouts up as paper cards.
The kettle is `assets/kettle.png` (the explainer's), so the close and the kitchen show the same kettle.

## layer-style
```
One single flat cut-paper object for a handmade paper diorama, in exactly the paper finish and palette of the attached reference image: matte construction paper, soft fibrous texture, gently irregular hand-cut edges, flat simple shapes, minimal detail. Seen straight on, front view, perfectly flat, no perspective. The object is centred and fills about 80% of the frame. The background is one perfectly flat, even, solid pure magenta #FF00FF from edge to edge: no shadow, no gradient, no table, no floor, no texture, no vignette. Nothing else in the image. Palette for the object only: paper #F7F1E8, soft ink #403C36, Kettle green #297A5C, warm yellow #E8C77A. No magenta or pink anywhere on the object. No pure black, no pure white, no red, no orange, no gloss. Absolutely no text, letters, numbers or logos. No people, no faces, no hands.
```

## layer-window
```
A kitchen window cut from paper: a square window with a soft ink paper frame and a cross of ink glazing bars dividing it into four panes, the panes warm yellow #E8C77A like morning light, with a thin cream paper sill along the bottom.
```

## layer-counter
```
The front of a small kitchen counter and stove unit cut from cream paper, a wide low rectangle about three times wider than tall. On the right third, a simple oven door cut from soft sage green paper (#9DB39B) with one short thin ink handle bar near its top. On the left two thirds, two plain cream cupboard doors with small round ink knobs. A thin soft ink paper strip along the top edge as the worktop edge.
```

## layer-mug
```
A plain coffee mug cut from Kettle green paper, side view, handle on the right, a thin cream rim line at the top.
```

## layer-plant
```
A small potted plant cut from paper: a cream paper pot with a thin ink rim, and five simple pointed leaves in Kettle green of slightly different shades rising from it.
```

## layer-steam
```
Three soft cream paper steam wisps, each a gentle S-shaped curl, rising side by side, tallest in the middle, with small gaps between them.
```

## layer-thumbs
```
A thumbs-up symbol cut from Kettle green paper as a plain rounded sticker shape: a soft rounded fist block with one rounded thumb pointing straight up, cut off flat at the bottom with no wrist, no arm, no sleeve, no fingernails, no skin tone. It reads as an emoji-style sticker, not a hand.
```

## layer-map
```
A picture map cut from paper, seen from directly above, as one wide flat rectangular sheet about twice as wide as tall with gently torn edges: a cream paper ground, soft Kettle-green paper fields in rounded patches, a winding pale blue-grey paper river crossing from top to bottom near the middle, and a faint dotted ink path winding from the left edge to the right edge. No roads, no labels, no buildings, no compass.
```

## layer-city
```
A small cluster of three cream paper city apartment buildings side by side, different heights, the tallest in the middle, flat front view, each with neat rows of small soft ink windows, a few windows warm yellow.
```

## layer-house
```
A small single-storey house cut from paper, flat front view: cream walls, a Kettle-green pitched roof, a small green chimney, an ink arched door on the left, and one square kitchen window on the right glowing warm yellow.
```

## layer-hills
```
A wide low strip of gently rolling hills cut from Kettle-green paper, two overlapping layers of slightly different greens, about five times wider than tall, flat along the bottom edge.
```

## layer-tree
```
One simple round tree cut from paper: a round Kettle-green canopy and a short soft ink trunk, flat front view.
```
