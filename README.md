# Claude Code skills

Custom [Claude Code](https://docs.claude.com/en/docs/claude-code) skills for video production and motion
design. Each skill is a folder with a `SKILL.md` (what Claude reads) plus any scripts and reference docs it
uses.

## Catalogue

### Video

| Skill | What it does | Use it when you say… |
|---|---|---|
| [video-logo-removal](skills/video/video-logo-removal) | Removes logos / brand prints from clothing and objects in real footage (SAM 2 tracking + LaMa inpainting + temporal stabilization), with QA tools for leftovers and playback shimmer. Runs locally (Apple Silicon or NVIDIA). | "remove the logo on his jacket", "clean the branding off the uniform and the bag" |
| [blog-to-video](skills/video/blog-to-video) | Turns a blog post into a Remotion video: brand setup, voice-over script, Whisper timing, scene generation, render. Invoke it explicitly (`/blog-to-video`). Install it into your Remotion project's `.claude/skills/` (manual install below). | "make a video from this blog post" |

### Motion design

| Skill | What it does | Use it when you say… |
|---|---|---|
| [saas-motion-ideation](skills/motion-design/saas-motion-ideation) | Pre-production for SaaS marketing animation: concepts, visual metaphors, narrative structure, storyboards. | "brainstorm a launch video for this feature", "storyboard an explainer" |

## Install

**As a Claude Code plugin (recommended)** - in Claude Code:

```
/plugin marketplace add harishwtf/skills
/plugin install video-logo-removal@harishwtf-skills
/plugin install saas-motion-ideation@harishwtf-skills
```

Each skill is its own plugin, so install only what you need. `/plugin` then lets you browse the catalogue.

**Manually** - copy (or symlink) a skill folder into `~/.claude/skills/` (personal) or
`.claude/skills/` in a project:

```bash
git clone https://github.com/harishwtf/skills.git harishwtf-skills
cp -r harishwtf-skills/skills/video/video-logo-removal ~/.claude/skills/
cp -r harishwtf-skills/skills/video/blog-to-video  my-remotion-project/.claude/skills/
```

Some skills need a one-time setup step; it is described at the top of their `SKILL.md`.

## Layout

```
skills/
  video/            video production pipelines
  motion-design/    creative direction and pre-production
.claude-plugin/
  marketplace.json  plugin catalogue for /plugin marketplace add
```

Adding a skill: put its folder in the category that fits (or create a new category), add a row to the
catalogue above and an entry to `.claude-plugin/marketplace.json`, then check with `claude plugin validate .`
