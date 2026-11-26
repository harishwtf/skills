# Style language

What the look is made of, so you can judge an image and steer a retry.

## The locked look

This is what the owner approved. Everything in the style lock sentence maps to
one of these.

- **Line:** black brush-pen outline with a slight wobble and uneven weight, a
  little heavier than you would expect. Closed, confident shapes. No sketchy
  double lines, no pencil texture.
- **Tone:** two values only, black ink and white paper. No grey, no hatching
  used as shading, no gradients, no cast shadows.
- **Fills:** flat solid black for hair, one garment, and a handful of objects.
  The balance of black shapes against white space is the composition.
- **Skin:** left as white paper. No skin tone is drawn.
- **Faces:** minimal. Dot or simple almond eyes, short brows, a single-line
  nose, a small mouth. Glasses, a beauty mark, earrings or a bindi do a lot of
  work.
- **Bodies:** slightly off proportions: head a touch large, limbs a touch
  long, hands oversized and expressive.
- **Objects:** drawn as clear, nameable silhouettes with a few interior lines.
  Patterns (dots for grains, lines for wood) stay sparse.
- **Space:** pure white background, generous margins, at most one line for a
  floor or counter. No scenery behind the subject.
- **Life:** short motion ticks and steam curls. No speech bubbles unless asked.
- **Text:** none, unless the writing is the subject of the picture.

## Notion's stroke, up close

What the drawings on Notion's own "about" page look like when enlarged. This is
the texture the owner asked for by name.

- **Line:** a brush-pen line with real thick-and-thin. It swells on curves and
  tapers to a point where the pen lifts. Edges are slightly rough. Some shapes
  are not fully closed.
- **Faces:** tall simple ovals. Eyes are two small dots or short dashes. The
  nose is one long line, often with a small hook. The mouth is a short curve.
  A moustache is a single black shape.
- **Hair:** one solid black blob with two or three flicks for a quiff or a
  fringe. No strands.
- **Clothes:** white shirts drawn as outline, trousers as solid black shapes,
  shoes as a couple of lines.
- **Hands:** quick, with splayed finger lines rather than modelled fingers.
- **Objects:** thin outlined shapes, slightly out of square, with only the
  detail needed to recognise them (a paperclip, a lightbulb, a page of lines).
- **Ground:** one ruled baseline under the scene, nothing else.
- **Detail level:** low. Far fewer lines than a careful drawing would use.

## What the source material shows

Notes from Notion's own pages and writing about its illustration, kept as
traits rather than anything to copy.

- The original work was all black and white; colour arrived later and only in
  advertising.
- It was meant to stand apart from the smooth vector illustration other
  companies used: minimal, with a gestural, hand-made line.
- Ideas are shown through metaphor rather than explained: a head in profile
  surrounded by small icons for "thinking", tools and paper flying around a
  figure for "work".
- Closer framing feels more personal than small figures seen from far away.
- Figures share similar proportions and carry no skin colour.
- Scenes often sit on a single baseline rule with icons and props radiating
  around a small full-length figure with a big black hair shape, white shirt
  and black trousers.
- The tone is smart and a little whimsical, never cute.

## Optional dials

Off by default. Turn one on only when the user asks for it, and keep it the
same across a whole set.

| Dial | What to add to the prompt | Seen in |
|---|---|---|
| One accent colour | "a single flat accent colour, [colour], used on one or two objects only, everything else black and white" | hand-drawn office doodles with one orange or yellow |
| Halftone tone | "one area filled with a coarse black halftone dot screen instead of solid black" | bold figure with screen-tone trousers |
| Ground shadow | "a flat solid black blob under the object as a ground shadow" | chunky outlined icon sets |
| Hatching | "a little loose pen hatching on hair and ears" | quick pen cartoons |

The loose, hand-drawn line is not a dial. It is part of the lock (the
HAND-DRAWN STROKE block) and goes in every prompt.

### Textured stroke (the "v2" look)

The owner asked for a version with "a bit more textury, a little more
hand-drawn" stroke, saw it across a full set of six, and then chose to keep the
standard stroke as the default. So this is a dial: use it only when they ask
for the textured or "v2" look. It replaces the standard HAND-DRAWN STROKE block
for that image or set.

```text
HAND-DRAWN STROKE:
drawn by hand with a real brush pen on paper: confident calligraphic outlines
that swell and taper, visible dry-brush texture with broken bristle marks along
the edges and at the ends of strokes, slightly uneven ink inside the thick
lines and black shapes so a little paper shows through, a gentle natural
wobble, a few lines left open or overlapping at the corners, restrained and
elegant rather than messy, very simple cartoon face, minimal interior detail,
no fine hair strands, no cross-hatching, no scribbling, no drawn surface
textures on objects
```

As with the standard block, drop the face and hair phrases when there is no
person. It produces visible bristle texture inside black areas and rougher,
more broken line ends. Name the solid black items explicitly, because this
block tends to leave scenes lighter on black.

The accent-colour dial needs an explicit request each time. The owner has
already turned down colour once, on a brand mark, so never offer it unprompted.

## Common ways it goes wrong

| What came back | What to change |
|---|---|
| Soft grey shading or texture | Add "no grey tones" and repeat "flat solid black fills" in the subject |
| Clean, even vector-icon line | Check the HAND-DRAWN STROKE block is in the prompt, word for word |
| Tidy, detailed editorial line art | Same, and add "drawn simply with few lines" to the props |
| Painterly or realistic face | Specify "two small dot eyes, long simple single-line nose, small curved closed smile" |
| Image looks almost all black | It has a transparent background; add a white backing and export again |
| Emblem off-centre or overlapped | Clear the surface (move hair and props), say "exactly in the centre … level and horizontally centred" |
| Gibberish on jars, boxes, bags | Add "all labels are blank shapes with nothing written on them" |
| Crowded, hard to read | Cut the item list, name which items are solid black, ask for more margin |
| Everything outline, looks thin | Name three or four things to fill solid black |
