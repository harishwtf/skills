# Video Types

## Listicle (Supported)

**Use for:** "N Best X", "Top N Y", "N Leading Z" blog posts

**Structure:**
```
S01_Intro         — Hook + problem statement + "Here are the N best..."
S02_Platform1     — PlatformScene with strengths, limitation, pricing, G2
S03_Platform2     — ...
...
S{N+1}_PlatformN  — Last platform
S{N+2}_Conclusion — Static outro image (120 frames)
```

**Components used:**
- `PlatformScene.tsx` — reusable template for each item
- `WordReveal.tsx` — staggered word animation for intro
- `FadeIn.tsx` — generic fade+slide wrapper
- `Conclusion.tsx` — static outro

**Data config:** `platforms.json` with array of platform objects

---

## Explainer (Planned)

**Use for:** Product launches, feature announcements, how-it-works videos

**Structure:**
```
S01_Hook          — Attention-grabbing problem/question
S02_Problem       — Pain points with visual metaphors
S03_Solution      — Product reveal + key value prop
S04_Feature1      — Feature deep-dive with animation
S05_Feature2      — ...
S06_CTA           — Call-to-action + outro
```

**Would need:**
- New scene components (HookScene, ProblemScene, FeatureScene, CTAScene)
- Different data config format (features.json)
- More complex animation patterns (demos, screenshots, UI animations)

---

## Comparison (Planned)

**Use for:** "X vs Y" blog posts, product comparisons

**Structure:**
```
S01_Intro         — "Which is right for you?"
S02_Overview      — Side-by-side comparison grid
S03_Category1     — Deep-dive comparison on topic
S04_Category2     — ...
S05_Verdict       — Winner reveal + recommendation
S06_Conclusion    — Static outro
```

**Would need:**
- ComparisonScene component (split-screen layout)
- VerdictScene component
- Different data config (comparison.json)
