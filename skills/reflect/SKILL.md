---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Before fanning out, find this conversation's transcript. Sessions for this workspace live under `~/.grok/sessions/<percent-encoded absolute cwd>/<session-id>/`. Percent-encoding turns `/` into `%2F`, so `/Users/you/proj` is `%2FUsers%2Fyou%2Fproj`. Each session directory holds `chat_history.jsonl` and `updates.jsonl`. `GROK_HOME` overrides `~/.grok`. Do not glob `~/.grok/sessions/*/`. That crosses workspace boundaries and reads private chats from unrelated projects.

```bash
encoded=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$PWD")
ls -t "${GROK_HOME:-$HOME/.grok}/sessions/$encoded"/*/chat_history.jsonl 2>/dev/null | head -10
```

Read the first lines of each candidate. Take the file whose opening user message matches this conversation. If none matches, pass a tight digest of the session instead.

## 2. Spawn three reviewers in parallel

One message, three `spawn_subagent` calls, omit `subagent_type`, the default tool set. Do not pass a readonly flag. Reviewers need MCP, which stays available through `search_tool` and `use_tool`.

Each reviewer and the synthesizer name a role line in the `pstack-models.md` rule and a default. Set `model` to that line's value, or to the default if the rule or the line is missing. Leave `model` unset when the value is `auto` or `inherit-parent`. If `spawn_subagent` has no `model` argument, omit it for this session so the child inherits the parent, and apply step 1 of **setup-pstack** so the next session can pass `model`. If it rejects a slug, use the closest slug from `grok models` and say so. Pick each subagent's reasoning effort for the job, per the Subagents section.

| Lens | Role line | Default `model` | Prompt template |
|---|---|---|---|
| Judgment | `reflect judgment, divergent, synthesizer` | `grok-4.6` at `xhigh` | `references/judgment-reviewer.md` |
| Tooling | `reflect tooling` | `grok-4.6` at `xhigh` | `references/tooling-reviewer.md` |
| Divergent | `reflect judgment, divergent, synthesizer` | `grok-4.6` at `xhigh` | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the `spawn_subagent` response body.

## 3. Synthesize

One `spawn_subagent` call, omit `subagent_type`, `model` from the `reflect judgment, divergent, synthesizer` line (default `grok-4.6` at `xhigh`), the default tool set. Do not pass a readonly flag. It spot-verifies citations through MCP via `search_tool` and `use_tool`. Pass `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog. See the **encode-lessons-in-structure** principle skill.

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit. The user picks the subset and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

File each Backlog item to your team's devex or backlog tracker without waiting. Only the Accepted list waits for approval.

Never edit a skill under `plugins/cache/`. Before approval, show its destination, `.grok/skills/<skill>/` or `~/.grok/skills/<skill>/`. After approval, copy the skill folder there and edit the copy. Never open a PR or push.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to Grok Build's `/create-skill` skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `create-skill` and run its description-optimization loop.
- `new skill via create-skill: <kebab-name>`: hand creation to `create-skill`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
