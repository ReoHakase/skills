---
name: agentskills-authoring
description: >-
  Author, review, or refactor Agent Skills per agentskills.io: valid SKILL.md
  frontmatter (name matches directory, description at most 1024 characters),
  optional scripts/references/assets, progressive disclosure (keep SKILL.md body
  under roughly 500 lines and 5000 tokens), description trigger tuning, and
  eval-driven output quality (evals/evals.json, assertions, grading). Use when
  creating skills from scratch, fixing spec violations, splitting overflow into
  references/, optimizing the description field, or setting up structured
  evaluations.
---

# Agent Skills authoring (agentskills.io)

Follow the official [Agent Skills specification](https://agentskills.io/specification) and the skill-creation guides. **Verbatim reference copies** live under `references/` in this skill—open the file that matches your question before improvising.

| Topic                                                                                    | Read                                                                           |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Format, naming, frontmatter, directories, progressive disclosure, validation             | [references/specification.md](references/specification.md)                     |
| Grounding in expertise, scope, tokens, calibration, patterns (gotchas, templates, loops) | [references/best-practices.md](references/best-practices.md)                   |
| `description` field, trigger evals, train/validation split, optimization loop            | [references/optimizing-descriptions.md](references/optimizing-descriptions.md) |
| Test cases, with/without skill runs, assertions, grading, benchmarks, iteration          | [references/evaluating-skills.md](references/evaluating-skills.md)             |

## When this skill applies

Use it for **structuring and validating** skills (metadata, layout, disclosure, triggers, evals). It does not replace domain expertise—skills should still be grounded in real workflows and project artifacts; see best-practices.

## Authoring workflow

1. **Ground the content** — Prefer extracting from a solved real task or synthesizing from internal docs, APIs, and failures—not generic platitudes. See _Start from real expertise_ in [best-practices](references/best-practices.md).

2. **Create or fix the directory** — Parent folder name must equal `name` in frontmatter (lowercase `a-z`, digits, single hyphens, no leading/trailing hyphen). Minimum file: `SKILL.md`.

3. **Frontmatter** — Required: `name`, `description` (1–1024 chars, both _what_ and _when_, keyword-rich). Optional: `license`, `compatibility` (≤500 chars if present), `metadata`, `allowed-tools` (experimental). Details: [specification](references/specification.md).

4. **Body** — Keep `SKILL.md` lean (under ~500 lines / ~5000 tokens). Move depth to `references/` or `assets/` and **tell the agent when** to load each file (conditional progressive disclosure). Link **one level deep** from `SKILL.md` to referenced files.

5. **Calibrate prescriptiveness** — Fragile sequences: exact steps or scripts. Flexible reviews: goals and checks. Prefer **one default tool or path** plus a short escape hatch, not a menu of equals.

6. **Validate** — Run `skills-ref validate ./skill-directory` when the CLI is available ([specification#validation](references/specification.md)).

7. **Tune triggering** — Treat `description` as the trigger surface (agents often load only name+description first). Use imperative “Use when…” phrasing, user-intent focus, and explicit edge contexts. Build ~20 should/should-not queries; consider train/validation split to avoid overfitting. Full process: [optimizing-descriptions](references/optimizing-descriptions.md).

8. **Evaluate output quality** — Add `evals/evals.json`, run with vs. without skill (or vs. old version), add **assertions after** you see real outputs, grade with evidence, aggregate `benchmark.json`, use human review for non-assertable quality. Iterate on `SKILL.md` from failures + traces. Full process: [evaluating-skills](references/evaluating-skills.md).

## Omit what agents already know

Once a skill loads, every token competes with the rest of the context window. **Default assumption:** the agent already knows mainstream programming, common file formats, and generic “best practices.” Skills earn their space with **project- and environment-specific** facts the model would not infer reliably.

**Leave out** introductory explanations of universal ideas (for example what HTTP is, what a PDF or migration is, or vague advice like “handle errors properly”). **Keep in** non-obvious procedures, exact commands or APIs, naming mismatches across systems, soft-delete rules, health vs. readiness endpoints, org conventions, and **gotchas** that contradict normal assumptions.

**Decision test** (from [best-practices](references/best-practices.md), _Spending context wisely_): for each paragraph or bullet, ask—_Would the agent get this wrong without this instruction?_ If **no**, delete or shorten it. If **unsure**, run a quick eval or compare with vs. without the skill; if quality is unchanged, omit it.

Verbose generic filler makes skills _longer_ but not _smarter_—it dilutes the signal and can trigger wrong branches (“instructions that don’t apply to the current task”). Prefer one concrete default plus a short escape hatch over encyclopedic coverage.

## Quick checklist

- [ ] Directory name matches `name`; `name` meets character and hyphen rules
- [ ] `description` ≤1024 chars; states capabilities and trigger scenarios; not vague (“Helps with X”)
- [ ] `SKILL.md` body sized for progressive disclosure; overflow in `references/` or `assets/` with explicit load conditions
- [ ] File links from `SKILL.md` are relative and one level deep
- [ ] Optional `scripts/` helpers are documented; bundling repeated logic preferred over one-off regeneration
- [ ] Gotchas for non-obvious project facts live where the agent will see them before mistakes
- [ ] No padding with universal background; each block passes “would the agent get this wrong without it?”
- [ ] After substantive edits: consider trigger evals and/or output evals as appropriate

## Official links

- [Specification](https://agentskills.io/specification)
- [Best practices](https://agentskills.io/skill-creation/best-practices)
- [Optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
- [Evaluating skills](https://agentskills.io/skill-creation/evaluating-skills)
- Docs index: [https://agentskills.io/llms.txt](https://agentskills.io/llms.txt)
