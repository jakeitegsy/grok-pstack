# benny

benny gives you two wakes for slack issue reports. one triages each report. the other reproduces confirmed bugs and may prepare a small draft fix. grok build has no automations editor. a live wake is `/loop` or `scheduler_create`, and only when you ask.

the files in this directory are dormant setup and automation sources. they do not appear as slash skills.

## set it up

1. point grok build at [`FOR_AGENTS.md`](./FOR_AGENTS.md) and name the target repository.
2. let setup merge this whole directory into the target at `.grok/automations/benny/`. it must preserve destination-only files and review conflicts instead of overwriting local edits.
3. let setup enable pstack with `grok plugin enable pstack`, or with this `.grok/config.toml` for shared dependencies:

```toml
[plugins]
enabled = ["pstack"]
```

4. keep user-owned configuration outside the copied pack, for example in `.grok/benny/`. adapt [`configuration.example.yaml`](./templates/configuration.example.yaml) and [`feature-map.example.md`](./skills/reproduce-and-fix-issues/references/feature-map.example.md).
5. commit `.grok/config.toml`, `.grok/automations/benny/`, and any secret-free configuration before enabling either automation.
6. review each new wake draft. install it with `/loop` or `scheduler_create` only when you ask. then send a harmless test report and verify every source-channel post stays in the original thread.
