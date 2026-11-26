---
name: notion-style-illustration-v2
description: >
  Version 2 (textured stroke) of the Notion-style illustration skill. Create
  original black-and-white ink-line illustrations in the "Notion style" look
  with a textured dry-brush line: bristly brush-pen outlines that swell and
  taper, black shapes with a little paper showing through, simple cartoon
  faces, lots of white space, no shading and no colour at all. Use this
  whenever the user asks for Notion-style or Notion-like illustrations,
  characters, avatars, spot illustrations, onboarding, feature or empty-state
  art, hand-drawn black-and-white line art, the "textured" or "v2" look, or
  more illustrations for M in that look, even if they never say "Notion". Also
  use it to put a logo or emblem into one of these illustrations. This skill
  only ever produces this one look. If the v1 skill is also installed, use this
  one only when the textured, dry-brush or v2 look is asked for.
---

# Notion-style ink-line illustration (v2, textured stroke)

This skill makes one look and nothing else: original black-and-white
illustrations that feel drawn by hand with a brush pen. It exists because the
owner tried this look, liked it, corrected it, and wants every future
illustration to match.

Read the reference files when you need them:

- `references/prompt-patterns.md` — fill-in templates for people, hands,
  objects, cards, notes with writing, shelves, emblems, sets and sheets.
- `references/examples.md` — the exact prompts that produced the v2 set.
  Start from the closest one.
- `references/style-language.md` — what the look is made of, what Notion's own
  drawings show up close, and the optional dials.

## The style lock

Every prompt carries both blocks below, word for word. The approved images came
from this wording, so paraphrasing is the fastest way to lose the look.

**1. The base sentence** (goes at the end of the character anchor, or under
`STYLE:` for pictures without people):

```text
monochrome hand-drawn ink illustration style with wobbly brush-pen outlines of
uneven line weight, flat solid black fills, unshaded paper-white skin, pure
white background, no shading, no gradients, no colour
```

For pictures with no people, swap `unshaded paper-white skin` for
`unshaded paper-white surfaces` and add `no grey tones`.

**2. The hand-drawn stroke block** (its own paragraph in the prompt):

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

Drop `very simple cartoon face` and `no fine hair strands` when there is no
person in the picture.

This is the textured version of the stroke. The owner asked for a line that was
"a bit more textury, a little more hand-drawn, and tastefully done", and this
wording produced it: bristle texture inside the black areas and rougher, more
broken line ends, without tipping into mess. Two habits go with it. End every
prompt with `opaque white paper background`, and name exactly which items are
solid black, because this block tends to leave scenes lighter on black.

The stroke block is not optional. Without it the model drifts toward tidy,
detailed line art with realistic faces, and the owner sent that back asking
for "the hand-drawn texture, style, and stroke that Notion has".

Describe the look; never name a company or an artist in the prompt. Naming a
brand invites the model to draw that brand's logo or imitate specific drawings,
and the point here is original work in a general ink-line genre.

## No colour, anywhere

Strictly black ink on white. That includes logos and emblems: the owner was
shown a version with the brand mark in its brand purple and said they did not
want any colour in it. If someone asks for colour, say this skill is
black-and-white only and offer the black version; add colour only if they
insist after hearing that.

## Workflow

1. **Read the brief as a list of pictures.** One idea per image. If one line of
   the brief holds two ideas (often split by a semicolon), make both and label
   them `a` and `b` rather than cramming them into one frame.
2. **Write the prompt** from the closest pattern or example. People get a
   CHARACTER ANCHOR, the HAND-DRAWN STROKE block and a SHOT VARIABLE; object
   scenes get a SUBJECT, the stroke block and the STYLE sentence.
3. **Generate** (see "Generating" below).
4. **Look at the full-resolution file**, not the thumbnail, and check it
   against the quality bar. Retry what fails.
5. **Deliver** the files, numbered in the order of the brief, with the anchors
   used.

Only ask the user a question when the answer changes who the person is or
which account pays for generation. Everything else has a sensible default
here, so pick it and say what you picked.

## Prompt structure

People:

```text
CHARACTER ANCHOR:
[name], [who they are and age range], [face shape], two small dot eyes with
[brows], long simple single-line nose, small curved closed smile, [marks,
jewellery, glasses], [hair as one solid black shape], [build and hands],
<base sentence>

HAND-DRAWN STROKE:
<stroke block>

SHOT VARIABLE:
[pose and action], [framing], [outfit, with one garment solid black],
[props and setting, drawn simply with few lines], [expression],
[motion ticks], generous white space, no text, no logos, no extra characters
```

Objects and scenes without people:

```text
SUBJECT:
[what is in the picture, item by item, each a different shape, drawn simply
with few lines], [which things are filled solid black for contrast], [how it
sits in white space], no people, no text, no lettering, no labels, no logos

HAND-DRAWN STROKE:
<stroke block without the face and hair phrases>

STYLE:
<base sentence, surfaces version>
```

Keep the anchor identical every time the same person appears. Put everything
that changes (pose, outfit, setting) in the shot variable.

## What makes the look work

- **Simple beats detailed.** A face is two dots, one long nose line and a small
  smile. Hair is one black shape, not strands. Props get a handful of lines.
  If it looks like careful editorial line art, it is too detailed.
- **The line has a hand in it.** Thick where the brush presses, thin where it
  lifts, bristly and broken at the ends, not always closed. Black areas are
  brushed in, so a little paper shows through.
- **Black is the only tone, so place it on purpose.** Hair, one garment, and a
  few objects go solid black; everything else is outline on white. Say which.
- **White space is part of the drawing.** Ask for generous margins and let the
  subject float. A single line is enough for a counter or a floor.
- **Every object a different shape and height.** Distinct, nameable things
  (baguette, pineapple, egg carton) read better than "groceries".
- **Short motion ticks** add life: a few strokes near a pan, a lifted bag, a
  pencil tip.
- **Hands are oversized and expressive.** A hand entering the frame with a
  solid black sleeve cuff is a complete illustration on its own.
- **Say no to text every time**, including "no labels" and "blank labels" for
  jars, boxes and bags. The model adds gibberish lettering otherwise.
- **When writing is the point**, quote the exact words, say how many lines,
  and check the spelling at full resolution. Three short words work well; a
  paragraph will not.

## People

Skin is left as unshaded white paper in this look, so who someone is has to be
carried by line: hair shape, a few facial marks, clothing, jewellery, and what
surrounds them.

**Default cast: Indian.** The owner asked for the people in M's illustrations
to look Indian, so unless told otherwise draw people that way, with specific
and respectful detail rather than a single token: for example centre-parted
hair in a low bun or a braid, a bindi, jhumkas, bangles, a nose stud, a kurta
or saree, a moustache or a short beard, and a setting to match (kadai, masala
dabba, rotis, steel tumblers). If the user names a different person or place,
follow that instead.

## Logos and emblems

The emblem should look drawn by the same hand as the rest of the picture, sit
dead centre on its surface, and be black. A crisp vector pasted on top, placed
off-centre, in colour, was rejected.

1. **Have the model draw it, described as geometry.** Give the emblem its own
   paragraph: where it sits ("exactly in the centre of the apron bib, level and
   horizontally centred"), that it is "drawn in the same brush-pen hand", its
   shapes in plain words, "clear white [surface] all around the emblem", and
   "nothing else on the [surface], no pocket, no pattern". Never use the brand
   name or a letter as text; describe the shape.
2. **Clear the surface first.** Face the torso straight on and keep hair, hands
   and props off the panel. A braid over the shoulder ran across the apron bib
   and pushed the emblem off-centre; a low bun fixed it.
3. **Check it against the real file.** Crop the emblem from the full-resolution
   image, enlarge it, and compare shape by shape with the actual logo. Retry if
   the shapes are wrong.
4. **Composite only when it cannot be drawn.** For a detailed logo or a
   wordmark that must be exact, generate a blank panel instead and place the
   real vector on it in black, centred on the panel. Tell the user it will look
   crisper than the drawing around it.

**M's mark** is bundled at `assets/m-mark.svg` for checking against: a
horizontal pill about 2.4 times as wide as it is tall, with a wavy line cut
through its middle that starts low, rises over two rounded humps and ends low.
The wording that reproduced it correctly:

```text
EMBLEM:
exactly in the centre of the apron bib, level and horizontally centred, one
small emblem drawn in the same brush-pen hand: a horizontal pill-shaped capsule
badge about twice as wide as it is tall, filled solid black, with a single
smooth white wavy line running across its middle that has exactly two rounded
humps like a soft lowercase handwritten m; clear white apron all around the
emblem; nothing else on the apron, no pocket, no pattern
```

## Sets and consistency

- Use the same two lock blocks on every image in a set. An image made without
  the stroke block will look tidier than its neighbours.
- Reuse one anchor word for word across a set. Costume, hair and props hold
  well; fine facial identity drifts between generations, which matters less
  here because faces are so simple.
- For a recurring character, keep the approved image and, where the generator
  accepts an image as input, feed it back as a reference.
- Keep the whole set the same size and the same amount of white space.

## Generating

Use whichever image generator this session has. What is proven:

- **Figma `generate_image`**, model `gpt-image-2.5-flare`, 1024 × 1024. Use
  1024 × 1536 for a standing full-body figure. It needs a Figma file to place
  the image in; create a draft if there is none.
- With the `genmedia` CLI, `openai/gpt-image-2` is the closest equivalent.

Generation spends the user's credits. If they have not said in this
conversation which account or plan to use, ask once before the first image,
then carry on without asking again for that brief. Say how many images were
generated when you finish.

The preview a tool returns is a small thumbnail. Download the full-resolution
PNG straight away (links expire) and judge that.

**Check for a transparent background.** Some results come back as a PNG with
transparency instead of white paper; opened in a viewer they look almost
entirely black. If the file reports an alpha channel (`RGBA`), put a white
backing behind it before delivering: in Figma, add a white solid fill beneath
the image fill and export the frame.

## Quality bar

Retry or fix when:

- Anything is grey, shaded, gradient or coloured, or texture is drawn onto
  objects instead of living in the brush stroke.
- The texture has tipped into scribble, splatter or mess.
- The line is thin, even and tidy, or the face is detailed and realistic.
- Lettering, numbers, labels or a logo appear that were not asked for.
- Requested writing is misspelled or has extra lines.
- The scene is all outline with no solid black, or so much black it clogs.
- The subject touches the frame edge or there is no white space around it.
- A person does not read as who the user asked for.
- An emblem is off-centre, overlapped, the wrong shape, or not black.
- The file has a transparent background.

## Deliver

Save PNGs in a folder inside the user's project, numbered to match the brief
(`1-…`, `2a-…`, `2b-…`). Show them, list anything that came out differently
from the brief, give the anchors used so the same characters can be made
again, and say how many images were generated.

## Where the look comes from

"Notion style" is used here as shorthand for a genre: minimal black-and-white
ink illustration with a hand-drawn line. Notion's own illustrations were
originated by the illustrator Roman Muradov and are drawn by hand. This skill
does not copy those drawings, does not put Notion's name or marks in any
output, and its results should not be presented as Notion's or the artist's
work.
