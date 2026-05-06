---
name: conventional-commit
description: >-
  Use this skill whenever the user asks to commit, create commits, split staged
  changes, write commit messages, fix commitlint failures, or choose Conventional
  Commit types/scopes. It enforces Conventional Commits with exactly one Gitmoji,
  mandatory English body prose, optional GitHub `(#issue)` refs, no
  Context-style body labels, and Agent Skills / APM `feat` vs `docs` decisions.
  Covers `gh` issue sync, dry-run vs real commits, commitlint config, Changesets,
  and changelog tooling. Standalone.
compatibility: >-
  GitHub CLI (`gh`) optional for branch-based issue lookup. Bundled samples
  include Node `commitlint` (`assets/commitlint.config.ts`) and commitlint-rs
  (`assets/.commitlintrc.yaml`).
---

# Conventional commit authoring (Conventional Commits + Gitmoji)

Standalone guide for **staging, splitting, and committing** with messages that are **machine-readable** (Conventional Commits, changelog tools) and **human-scannable** ([Gitmoji](https://gitmoji.dev/) in the subject line).

## When to use

- Turning **already staged** changes into one or more commits with consistent headers
- Splitting work by **scope** / component so each commit is easy to revert and grep
- Repos using **commitlint**, **Changesets**, **release-please**, or **git-cliff**
- Issue-driven branches where the subject must carry **`(#123)`**
- **Agent Skills / APM** layouts (root-level `<skill-name>/SKILL.md`): picking **`feat` vs `docs` vs `fix`** without wavering—see [Agent Skills repositories (feat vs docs)](#agent-skills-repositories-feat-vs-docs)

## When not to use

- **Trivial one-line commits** where the user already pasted the exact final header and only needs `git commit -m` (the full split workflow does not pay for its overhead).
- **Pure preference** rewrites (“sounds nicer”) with no reliability or changelog impact—treat instruction-quality iteration elsewhere; this skill is for **commit shape and hygiene**, not subjective style debates alone.
- Environments where you **cannot** stage, split, or run git hooks and the user only wanted a **dry message**—honor that and skip the multi-step workflow.

---

## Commit workflow (agent)

Operate on **staged** changes unless the user asks otherwise.

1. **Refresh issue context** when the branch encodes an issue id and you might have missed nuance:  
   `gh issue view "$(git branch --show-current | grep -oE '^[0-9]+')" --json title,body`  
   (Adjust the regex if the repo uses prefixes like `issue/123-topic`; fall back to `gh issue view <id>` when ambiguous.)
2. **Choose split granularity**: one primary scope (and one logical concern) per commit; split cross-cutting edits across commits.
3. For **each** planned commit, prepare:
   - Full message (`type`, optional scope, optional `!`, Gitmoji, imperative English subject, optional `(#issue)`).
   - **Body** using the flat prose rules under **Body (English)** (short paragraphs, backticks on literals, no `Context/Changes/Impact` labels unless requested).
   - List of **paths** (and line ranges when helpful) touched by that commit—after splitting, restage per commit if needed.
4. **Output format**: for every commit, emit the **complete message** inside a fenced block, then **target files** (and ranges). Use English throughout the message.
5. **Important — multiple commits**: print **all** commit messages (and file lists) **before** running **`git commit`** the first time. Only then execute commits in order (restaging between commits as required).
6. **Execute commits** unless the user asked for a dry run only (`dry run`, `message only`, `no commit`, etc.): run `git commit` with the prepared messages after staging the matching paths.

---

## Message shape (required layout)

```
<type>[(scope)][!]: <gitmoji> <subject> [(#<issue>)]

<body — Markdown OK; required>

<footer — trailers only>
```

Examples:

- Scoped: `feat(web/ui): ✨ add numeric date picker (#482)`
- No scope: `docs: 📝 add CONTRIBUTING Gitmoji table (#702)`
- Repo-wide / initial: `feat: ✨ bootstrap published APM skill repository`
- Breaking: `feat(api)!: 💥 rename argument (#888)`

Omit empty **`()`** when there is no scope. Omit **`!`** when the change is non-breaking.

- **Body is required** for every non-`wip` commit, even tiny edits.
- **Blank line** between subject / body / footer.
- **Gitmoji**: exactly **one** primary emoji from [gitmoji.dev](https://gitmoji.dev/), placed **immediately after** the colon and space, **before** the English subject.
- **`(#<issue>)`**: include when the team ties work to GitHub issues—especially if **`git branch --show-current`** embeds that number (`123-topic`, `feat/456-x`, etc.). Omit only when there is no issue; never invent ids.
- **`Fixes #123` / `Closes #123`**: still use in the **footer** when merging should close the issue.

### Subject (English)

- After the Gitmoji: **imperative mood**, **lowercase** start of the verb phrase, **no trailing period**.
- Wrap identifiers / APIs / routes / filenames in **backticks** when it aids scanning.
- Keep the **whole header ~72 characters or fewer** when practical (Gitmoji consumes width).

### Body (English)

**Structure**

- Use **one short paragraph per idea**, separated by **blank lines**. Do **not** label sections (`Context:` / `Changes:` / `Impact:` / `Background:`) unless the user explicitly asks for that format.
- Typical flow still mirrors **why → what → follow-ups**, but **implicitly** across paragraphs rather than headings.

**Sentence style**

- **Sentence case**, **period** at the end of each sentence.
- Often open with the **constraint or symptom**, then the fix—sometimes as **two clauses in one line** joined by a **semicolon** when both are short:

  > `Raise minimum token scopes for workflow edits; pin third-party actions to immutable SHAs.`

- Equally common: paragraphs that **lead with an imperative verb** summarizing work (`Raise …`, `Add …`, `Pin …`, `Extend …`, `Provide …`, `Drop …`), especially when several independent edits belong in one commit.

**Markup and identifiers**

- Use **inline code** (backticks) for **paths**, **commands**, **identifiers**, **config keys**, and **narrow technical literals** (for example `src/auth/session.ts`, `pnpm-lock.yaml`, `.github/workflows/ci.yml`).
- Avoid Markdown **headings** and heavy bullet lists in the body; prefer prose. Use a **short bullet list only after `Notes:`** when caveats are orthogonal (extra upstream bumps, follow-up work).

**Length**

- Scale to the change: **tiny edits** use **one sentence**; multi-file behavior changes use **two–four tight paragraphs** (similar breadth to a focused `fix(ci)` or `feat(api)` that touches several files).

**Large migrations (upstream breakage, pins, lockfiles)**

When the change explains **why upstream broke**, **which issue threads matter**, and **what operators must do next**, stack **multiple prose paragraphs**:

1. Symptom + root cause, with upstream refs (`org/repo#NNN`) and error snippets in backticks.
2. Fix strategy (version bump, branch switch, config change) and why it is sufficient.
3. Operational fallout (deleted lockfile, regeneration command, CI caveat).

Use optional **`Notes:`** bullets only for caveats that sit beside the main story (semver pins, tool versions, scheduled follow-ups).

**Illustrative pattern — CI / automation** (fictional):

```
Raise GITHUB_TOKEN permissions so the github-actions manager can open PRs that touch workflow files (workflows scope is required alongside contents/pull-requests per the renovate GitHub Action docs).

Extend with helpers:pinGitHubActionDigests so actionable uses migrate to immutable commit refs with trailing version comments. Pin setup-node runtime lines via github-actions uses-with deps. Add versioningTemplate and descriptions on regex customManagers to satisfy recommended validation hygiene.
```

**Illustrative pattern — tooling migration** (fictional editor/plugin stack):

```
Neovim 0.12 removed the `all = false` compatibility option from `Query:iter_matches` (neovim/neovim#33070) and the legacy `master` branch of nvim-treesitter has been archived upstream and never adapted. That causes `attempt to call method 'range' (a nil value)` in `languagetree.lua:215` whenever treesitter parses a buffer (most visibly on markdown with fenced code blocks). See nvim-treesitter/nvim-treesitter#8618, neovim/neovim#39032.

AstroNvim v6.0 (2026-03-30) officially switched nvim-treesitter to the `main` branch which is Neovim 0.12 compatible. Bumping our pin from `^5` to `^6` pulls in the fix transitively. Local plugin overrides (`aerial`, `astrolsp`, `lazygit`) were checked against the v6 API surface.

`lazy-lock.json` is dropped because most of its pinned commits reference the now-frozen master branches (notably nvim-treesitter) and would conflict with the new main-branch resolution on first sync. Let `lazy.nvim` regenerate it on the next `:Lazy sync`.

Notes:
- AstroNvim v6 also updates AstroLSP to v4, mason-lspconfig to v2, and makes blink.cmp the default completion engine. Local AstroLSP tweaks are limited to the `servers` list and remain supported.
- nvim-treesitter `main` recommends tree-sitter-cli >= 0.26.1; CI still pins 0.25.10. Existing compiled parsers keep working but fresh `:TSInstall` runs may fail until the toolchain pin is raised — tracked as follow-up.
```

### Footer

- Plain trailers only: `BREAKING CHANGE: …`, `Fixes #…`, `Co-authored-by: …`.
- For reversions, reference the reverted commit SHA or original subject in the body.

---

## Types (semver / changelog)

Pick **by kind of change**, not by “importance”. Avoid masking a `fix`/`feat` as `chore`.

| type       | Typical changelog bucket |
| ---------- | ------------------------ |
| `feat`     | Added / Features         |
| `fix`      | Fixed                    |
| `perf`     | Changed                  |
| `refactor` | Often omitted            |
| `docs`     | Often omitted            |
| `style`    | Often omitted            |
| `test`     | Often omitted            |
| `build`    | Often omitted            |
| `ci`       | Often omitted            |
| `chore`    | Often omitted            |
| `revert`   | Yes                      |

### Agent Skills repositories (feat vs docs)

Repos that publish **installable skills** (for example **root-level** `<skill-name>/SKILL.md` and APM consumption) confuse **`feat` vs `docs`** because Markdown looks like “documentation.” Use this **default** to stop flip-flopping:

| Situation                                                                                                                                                                   | type                                                                                       | Rationale                                                                                                                                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **New** `<skill-name>/` directory (or equivalent first-time skill package)                                                                                                  | `feat`                                                                                     | You shipped a **new installable unit** / new consumer-facing capability in the registry. Scope with the skill id when the repo convention does (`feat(foo-bar): ✨ …`).                                                       |
| **`SKILL.md` / `references/` / `scripts/` / bundled assets** change **what agents do or read** (new section, new trigger wording, new required step, new script agents run) | `feat` (additive / expanded behavior) or `fix` (corrects wrong or misleading instructions) | These files are **executable instructions**, not marketing copy—treat instruction changes like product behavior. Use **`fix`** when the old text could cause incorrect runs; use **`feat`** when you add or widen capability. |
| **README**, root **install docs**, or **meta only** (no change to any `SKILL.md` / skill assets)                                                                            | `docs`                                                                                     | Publishing/consumer discovery text without altering skill behavior.                                                                                                                                                           |
| **Typo / formatting / table alignment** in `SKILL.md` with **no intended semantic change** to instructions                                                                  | `docs`                                                                                     | Truly editorial; if there is any chance behavior shifts, use `feat` or `fix` instead.                                                                                                                                         |
| Repo **tooling only** (`lefthook`, CI, `apm.yml` scaffolding) with **no skill instruction edits**                                                                           | `chore`, `ci`, or `build` (pick by kind)                                                   | Keeps skill commits grep-clean.                                                                                                                                                                                               |

**Decision test:** if an **`apm install …/skill-name`** checkout would **behave differently** for an agent after the change, the commit is **not** `docs`.

**Changelog tools:** `release-please`, **git-cliff**, and Changesets still read git history or fragments you configure—**subjects stay conventional**. Those tools do **not** change the **`feat` vs `docs`** split above; they add release metadata elsewhere.

---

## Type ↔ primary Gitmoji

| type       | Primary Gitmoji                                         | Use when                                                                                                                            | Prefer another type when                                                    |
| ---------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `feat`     | ✨ (⚠️ deprecations; 🔥 removals that deserve emphasis) | New user-facing capability or clear user value                                                                                      | Removal-only compat break → removal row below                               |
| `fix`      | 🐛 (🚑 hotfix; 🔒 security-sensitive fixes)             | Bug fixes, incorrect behavior, regression repair                                                                                    | Pure internal tidy → `refactor`                                             |
| `docs`     | 📝                                                      | README, guides, comments only; **see [Agent Skills (feat vs docs)](#agent-skills-repositories-feat-vs-docs) when `SKILL.md` moves** | Code, config, or **instruction-behavior** changes → matching `feat`/`fix`/… |
| `style`    | 🎨                                                      | Formatting, whitespace, non-functional polish                                                                                       | Risk of behavior change → `refactor` or `fix`                               |
| `refactor` | ♻️ (🗑️ dead-code cleanup)                               | Same behavior, clearer structure                                                                                                    | Goal is speed → `perf`                                                      |
| `perf`     | ⚡                                                      | Latency, memory, I/O wins                                                                                                           | Structure-only → `refactor`                                                 |
| `test`     | ✅ (🖼️ snapshot-only updates)                           | Adding / tightening tests                                                                                                           | Prod code fix → `fix`                                                       |
| `build`    | 📦 (combine with ➕➖⬆️📌 for deps)                     | Tooling, bundler, compiler deps                                                                                                     | Product logic → appropriate type                                            |
| `ci`       | 👷 (🔖 release automation)                              | Pipelines, caches, matrices                                                                                                         | Local-only build tweak → `build`                                            |
| `chore`    | 🔧                                                      | Meta/scripts with no runtime effect                                                                                                 | Touches behavior → real type                                                |
| `revert`   | ⏪️                                                      | Reverting a prior commit / PR                                                                                                       | Prefer forward fix → `fix`                                                  |

---

## Cross-cutting Gitmoji (pair with the table above)

| Emphasis           | Emoji       | When                               | Often paired with                     | Pitfalls                                         |
| ------------------ | ----------- | ---------------------------------- | ------------------------------------- | ------------------------------------------------ |
| Breaking           | 💥          | Highlight compat breaks            | `feat!`, `refactor!`, rarely `build!` | Still require `!` + `BREAKING CHANGE:` footer    |
| Security           | 🔒          | XSS/CSRF/authz/secrets             | `fix`, sometimes `build`              | Summarize CVE/risk/mitigation in body            |
| Dependencies       | ➕ ➖ ⬆️ 📌 | Add / remove / upgrade / pin       | `build(deps)` or `build(<pkg>)`       | Treat semver-breaking dep bumps as potential `!` |
| Accessibility      | ♿          | A11y fixes/features                | `feat`, `fix`, `style`, `docs`        | Mention SR/focus/contrast in body                |
| i18n/l10n          | 🌐          | Translations / locale plumbing     | `feat`, `fix`, `chore`, `build`       | Note sources, fallbacks, missing strings         |
| Release automation | 🔖          | Version / Changesets publish flows | `ci(release)`                         | Bot/workflow may rewrite commits anyway          |

---

### Tests: ✅ vs 🖼️

| Case              | Emoji | When                                                       |
| ----------------- | ----- | ---------------------------------------------------------- |
| General test work | ✅    | New cases, assertions, stability—anything beyond snapshots |
| Snapshot-only     | 🖼️    | Jest/Vitest/etc. snapshot deltas only                      |

If prod code changed too, prefer ✅ and mention snapshot updates in the body.

---

### Removals: 🔥 vs ⚠️ vs 🗑️

| Case                           | Emoji | type / markers                                       |
| ------------------------------ | ----- | ---------------------------------------------------- |
| Remove public API / route / UI | 🔥    | `feat!` or `refactor!` + `BREAKING CHANGE:`          |
| Deprecate but keep             | ⚠️    | Often `feat` or `docs` announcing sunset             |
| Dead code / unused assets      | 🗑️    | `chore` or `refactor`; use `!` if externally visible |

---

## Scope rules

- Use **kebab-case** segments; align with repo norms (`web`, `api`, `deps`, `release`, …).
- **First segment**: package or top-level area (`web`, `mcp`, `lib`, `domain`). Omit npm **`@scope/`** if the repo convention strips it.
- **Second segment**: recurring subdomain only (`ui`, `api`, `auth`, `db`, `page`, `deps`, `release`).
- **Avoid a third segment**—push detail into subject/body.
- For **repo-wide changes**, **initial commits**, or **formatting/tooling sweeps** that are not meaningfully owned by one package or sub-area, **omit the scope entirely**. Prefer `feat: ...`, `chore: ...`, or `style: ...` over artificial scopes like `repo` or `global`.
- **Split commits** instead of multi-scope monsters so `git revert` stays surgical.

**Heuristic**: adopt two-part scopes when at least **two** of these are true: you want `git log --grep`, the slice repeats across PRs, revert should be narrow.

---

## Breaking changes

Header carries **`!`**; footer carries machine-readable migration text:

```
feat(web/page)!: 🔥 remove `/pricing/discount` route (#999)

…

BREAKING CHANGE: `/pricing/discount` is removed; link to `/pricing` instead.
```

Optional **💥** in the subject reinforces the signal for humans; tooling still keys off **`!`** + **`BREAKING CHANGE:`**.

---

## Splitting commits

- Never mix unrelated scopes in one commit when separate staging is feasible.
- Prefer **one component / one cohesive command worth of change** per commit when the team tracks Cursor slash commands or UI components—name them in the subject/backticks when useful.
- Optimize for **easy revert**: config churn vs product logic should land separately.

---

## commitlint + Gitmoji

`@commitlint/config-conventional` expects a lowercase subject; a **leading emoji** often violates **`subject-case`** or related defaults.

- **Read the repo’s `commitlint.config.*`** before committing.
- A matching sample config is bundled at `assets/commitlint.config.ts`; copy it when the repo uses this skill's `type(scope): <emoji> <subject>` header shape.
- Recommended Node config behavior:
  - **Body required** via a custom `body-required` rule with a message that points agents to `conventional-commit/SKILL.md`.
  - **Gitmoji required** via a custom `gitmoji-required` rule that checks for an emoji immediately after `type(scope):`.
  - **`wip` bypass** via `ignores: [(message) => /^wip\b/i.test(message)]`.
  - **Skill hint** via `helpUrl` plus custom rule messages.
- Recommended commitlint-rs config behavior:
  - **Body required** via `body-empty: { level: error }`.
  - **Gitmoji required** as a YAML approximation via `description-format` requiring a non-ASCII prefix immediately after `type(scope):`.
  - **`wip` bypass** and **skill hint text** must live in the surrounding hook/wrapper because commitlint-rs YAML does not support Node-style `ignores`, custom rule messages, or `helpUrl`.
- Typical fixes: customize **`headerPattern`**, relax **`subject-case`**, or adopt a **Gitmoji-aware preset/plugin** if the repo standardizes on one.
- Subject suffix **`(#123)`** is usually fine unless a custom **`issue-pattern`** forbids it.

**Pre-commit hook pitfall**: declare **`additional_dependencies: ["@commitlint/config-conventional"]`** (and any Gitmoji preset packages) beside the hook so isolated installs resolve `extends`.

---

## Changesets

Changesets reads **`.changeset/*.md`**, not git subjects. **Gitmoji in commits does not affect Changesets parsing.**

| Concern                                            | Source                           |
| -------------------------------------------------- | -------------------------------- |
| Consumer-facing release notes / semver bump intent | Changeset fragments + Version PR |
| Git history / blame / commit-driven tooling        | Conventional + Gitmoji commits   |

Always add a **changeset** for user-visible package changes—even with polished commits. Mirror **major** bumps with **`!`** + **`BREAKING CHANGE:`** in git.

**release-please / git-cliff**: configure them to **consume conventional commits** or your cliff presets; they do **not** replace the [feat vs docs rules for skills](#agent-skills-repositories-feat-vs-docs)—they only **emit** or **parse** versions and notes from whatever history you feed them.

---

## Quick checklist

- [ ] Issue context skimmed via **`gh`** when branch implies an id.
- [ ] Split commits by scope/concern; restage between commits if needed.
- [ ] **`type(scope)!:`** correct; Gitmoji matches intent.
- [ ] English imperative subject; **`(#NNN)`** when applicable.
- [ ] Body is present and matches **Body (English)** (paragraphs, backticks); no `Context/Changes/Impact` headings unless requested; **large migrations** may use multi-paragraph narrative + optional `Notes:` bullets.
- [ ] Footer **`Fixes`/`Closes`/`BREAKING CHANGE:`** as needed.
- [ ] **All messages printed** before the first **`git commit`** when authoring multiple commits.
- [ ] **commitlint** / local hooks satisfied (Gitmoji may need custom rules).
- [ ] **Changesets** added for publishable package changes.
- [ ] **Agent Skills repos**: `feat` vs `docs` for skill dirs follows [Agent Skills repositories (feat vs docs)](#agent-skills-repositories-feat-vs-docs) unless the change is clearly README-only.

---

## Examples (headers only — monorepo)

Assume packages `@acme/web`, `@acme/mcp`, `@acme/lib`, `@acme/domain`:

```
feat(web/ui): ✨ add numeric date picker to `<Calendar>` (#482)
fix(web/auth): 🐛 normalize refresh failures to `401` (#513)
perf(web/api): ⚡ batch-fetch users on `GET /v1/users` (#601)
test(web/ui): ✅ cover `<Accordion>` keyboard navigation (#456)
test(web/ui): 🖼️ refresh icon snapshots (#789)
feat(web/page)!: 🔥 remove `/pricing/discount` (#999)
feat(mcp)!: 💥 rename `get_weather` argument to `location` (#888)
build(lib): ⬆️ bump `react` to v19.0.1 (#777)
revert: ⏪️ revert "feat(web/ui): ✨ add `<Toast>` for results (#666)"
docs: 📝 document commit conventions and Gitmoji in `CONTRIBUTING.md` (#702)
docs(cli): 📝 add `/test` command instructions (#800)
style(web/ui): 🎨 align spacing on `<Button>` and `<Input>` (#710)
fix(web/page): 🔒 escape HTML in profile `bio` (#745)
refactor(lib): ♻️ centralize auth token helpers (#720)
ci(release): 🔖 align Changesets commit messages with this spec (#730)
feat(web/api): ✨ add `fields` query to `GET /v2/users/{id}` (#740)
chore(lib): 🗑️ remove unused `useLegacyFetch` hook (#750)
refactor(domain/cart): ♻️ move cart totals into `price` module (#765)
feat(web/auth): ✨ add WebAuthn passkey sign-in (#760)
build(web): ➕ add `@storybook/addon-essentials` (#772)
build: ➕ add `lefthook` for git hooks (#772)
perf(web/ui): ⚡ virtualize `<DataTable>` rendering (#781)
feat(web/api): ⚠️ deprecate `POST /v1/session/refresh` (#770)
```

---

## Examples (body + footer)

Bodies below follow **Body (English)**: flat paragraphs, backticks on literals, no section labels.

```
feat(web/ui): ✨ add numeric date picker to `<Calendar>` (#482)

Event creation needed too many clicks and keyboard-first flows lagged; mobile and desktop date UX diverged.

Embed an inline numeric picker in `<Calendar>` with `ArrowLeft/Right/Up/Down` and `Home/End`. Add `aria-label` and `role="spinbutton"` so SR announcements stay accurate.

Legacy `<input type="date">` remains temporarily while screens migrate. Expect a small E2E cold-start regression from the added scenarios.
```

```
fix(web/auth): 🐛 normalize refresh failures to `401` (#513)

Expired refresh tokens sometimes surfaced `403`, which skipped client re-auth flows.

Return `401` consistently on revocation, attach `WWW-Authenticate` with `error="invalid_token"`, and split logs by failure reason so alerts stop false positives.

`onUnauthorized` handlers fire reliably; response shapes aside from status codes stay unchanged.

Fixes #513
```

```
feat(web/page)!: 🔥 remove `/pricing/discount` route (#999)

`/pricing/discount` duplicated v2 pricing content; drop the route, permanent `308` to `/pricing`, and refresh docs plus sitemap references.

Bookmarks keep working via redirect; SDKs that embedded the old URL must update integrations.

BREAKING CHANGE: `/pricing/discount` is removed—point integrations at `/pricing`.

Fixes #999
```

---

## Agent output template (per commit)

````markdown
#### Commit `k` / `n`

```text
<type>(<scope>): <gitmoji> <subject> (#<issue>)

<body required>

<footer optional>
```

**Paths**

- `path/to/file.ext` (lines 1–120)
````

---

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Gitmoji](https://gitmoji.dev/)
- [Keep a Changelog](https://keepachangelog.com/)
- [commitlint](https://commitlint.js.org/)
- [Changesets](https://github.com/changesets/changesets)
