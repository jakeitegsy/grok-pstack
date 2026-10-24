---
name: setup-pstack
description: Configure which models pstack uses per role and at what budget. Detects your available models and writes a user rule that overrides the skill defaults. Use for /setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack

Write `~/.grok/rules/pstack-models.md`. Every markdown file in `~/.grok/rules/` applies on every turn. The file sets pstack's model per role.

## Steps

### 1. Detect available models

Run `grok models` and read the `spawn_subagent` schema. The slugs `grok models` lists are the only real slugs you may write. Read each model's effort levels from `grok models` / `/model`. If you cannot detect any slug, ask the user to paste the slugs they have access to. Never write a real slug you have not confirmed. The aliases `inherit-parent` and `auto` are always valid even though they are not detected slugs. Both mean omit `model`.

When `spawn_subagent` lists `model`, pass it. When it does not, this session inherits the parent. Expose the argument for the next session before you finish setup:

- Leave the user config alone when `GROK_SUBAGENT_MODEL_INHERITANCE` is set, when `GROK_CONFIG` or `GROK_CONFIG_PATH` sets `features.subagent_model_inheritance`, or when `$GROK_HOME/requirements.toml` (default `~/.grok/requirements.toml`), `/etc/grok/requirements.toml`, or an MDM profile pins that key. Name the pin in the confirmation. This session omits `model`.
- Otherwise set `subagent_model_inheritance = false` under `[features]` in `$GROK_HOME/config.toml` (default `~/.grok/config.toml`). Preserve every other key and table. An explicit false overrides the remote default. The flag is read at session start, so this session still omits `model`.

Pass `model` only in a session whose schema includes it. Pass the effort only when `spawn_subagent` lists an effort argument. Otherwise the child inherits the parent's effort.

### 2. Load current state

The default role-to-model mapping is the rule shape shown in step 5 below. If `~/.grok/rules/pstack-models.md` already exists, read it and treat its `# budget` line and its role values as the current choices. Otherwise start from those defaults. A line whose role is not in step 5, such as `how critics`, is from a retired role. Drop it.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Prefer ask_user_question over free text. Offer these four options with these exact labels, and name the current budget when the rule records one. With no rule, say that `large` matches the skill defaults.

- `unlimited — max reasoning`
- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Build the working table from the skill defaults, and on a re-run keep any role you changed by slug, list, or alias (`inherit-parent`, `auto`). `unlimited`, `large`, `medium`, and `small` set the effort of every real model entry, panel entries included, to `max`, `xhigh`, `high`, or `medium`, on the ladder `max` > `xhigh` > `high` > `medium` > `low`. Effort is a separate field, written after the model id (`grok-4.6 xhigh`). If the model does not offer that effort, use its highest offered effort at or below the target, else mark the role as needing a choice. `inherit-parent` and `auto` do not change. So on grok 1.0.62, `unlimited` keeps `grok-4.6` at `xhigh`, `large` keeps the defaults, and `small` turns them into `grok-4.6 medium` and `grok-4.5 medium`. A panel list stays two entries when two different detected slugs exist. When the budget collapses a panel onto one slug, write that slug twice and tell the user the panel has no second model. If `spawn_subagent` has no `model` argument, still write the intended slugs. They take effect in the next session, after step 1 exposes `model`.

**(c) Show the roles and confirm.** Show every role with its model, marking any real slug not in the detected set as needing a choice. Also list each line step 2 dropped. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean this role runs on the parent chat model, so omit `model`) as the options. Prefer ask_user_question over free text. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list. Arena selects one value from it that differs from the parent's slug when another detected slug exists. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every real slug written must be in the detected set. `inherit-parent` and `auto` always pass. If a chosen real slug is not available, stop and ask again.

### 5. Write the rule

Write `~/.grok/rules/pstack-models.md` as plain Markdown. No YAML frontmatter. Include a `# budget` line and one line per role, using the same labels poteto-mode uses. Overwrite the whole file so re-runs stay idempotent. Shape for `large` when `grok-4.6` and `grok-4.5` are detected:

```
# pstack model configuration. One line per role. Delete a line to fall back to the skill default.
# `inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit `model`). Alias entries in a panel list still count toward its fan-out.
# Pass model only when spawn_subagent lists it. Step 1 exposes that argument for the next session.
# budget: large (xhigh)
feature, refactoring: grok-4.6 xhigh
bug-fix: grok-4.6 xhigh
perf-issue: grok-4.6 xhigh
hillclimb: grok-4.6 xhigh
judgment and prose: grok-4.6 xhigh
hardest tasks: grok-4.6 xhigh
how explorer: grok-4.6 xhigh
how explainer: grok-4.6 xhigh
why investigators: grok-4.6 xhigh
why synthesizer: grok-4.6 xhigh
reflect tooling: grok-4.6 xhigh
reflect judgment, divergent, synthesizer: grok-4.6 xhigh
arena runners: grok-4.6 xhigh, grok-4.5 high
arena cross-judge pool: grok-4.6 xhigh, grok-4.5 high
swarm workers: grok-4.6 xhigh
architect runners: grok-4.6 xhigh, grok-4.5 high
interrogate reviewers: grok-4.6 xhigh, grok-4.5 high
```

Substitute the slugs step 3 actually chose. Keep the role labels exactly as written above.

### 6. Confirm

Tell the user the rule was written and that it applies to new sessions. If you set `subagent_model_inheritance = false`, say that role models start in the next session and that this session still inherits the parent. If a pin blocked the flag, say that every role inherits the parent until that pin changes. Re-running this skill updates the file.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill` (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.

### 8. Offer a formal verification skill (optional)

Check whether the project already has a formal verification skill (a project skill that runs a model checker, a proof, or another verifier against the code). If not, offer once: "want a formal verification skill, so agents can prove a key property of your code holds in every case in scope, not only the cases tests reach? I can generate one with /create-formal-verification-skill." On yes, invoke `/create-formal-verification-skill` (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.
