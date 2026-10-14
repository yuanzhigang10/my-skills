# Verified Cursor CLI contract

The attachment was historically verified against CLI `2026.10.01-e373342`, the account's live `agent models`, and real Opus and Gemini 4 Argon inference. `agent` and `cursor-agent` are available; `cursor` alone tries to open an IDE and fails on that historical headless server.

Native invocation used by the helper:

```text
cursor-agent --print --output-format stream-json --mode ask \
  --model <advertised-model-id> --trust --sandbox enabled \
  --workspace <isolated-consultation-workspace> [--resume <cursor-session-uuid>]
```

The prompt is fed through stdin, not shell interpolation or an API-key argument. `--trust` applies only to the generated consultation workspace; it is not `--force` and does not grant write/shell access. The local project `.cursor/cli.json` denies `Read(**)`, `Write(**)`, `Shell(*)`, `Mcp(*:*)` and `WebFetch(*)`; supplied inline source makes tool access unnecessary. Do not copy source-repository hooks, MCP configuration or global auth into that workspace.

Local capability probe on 2026-10-13 used CLI `2026.10.01-e373342`, `--mode ask --sandbox enabled`, and all-tool-deny permissions. It exited 0 with a successful terminal result. This Mac supports that explicit sandbox mode for the consultation invocation; the helper enables it and fails visibly on errors rather than automatically disabling it. Model init labels establish Cursor routing; they do not independently audit the upstream implementation or sandbox enforcement internals.

`stream-json` provides a `system/init` with `model` and `session_id`, followed by a terminal `result` with `subtype=success`, `is_error=false`, assistant `result` text, and the same session ID. Preserve the ID at initialization, validate the terminal event, and then parse the assistant's requested findings JSON. CLI transport JSON is not itself the findings schema. Interrupted or nonzero runs retain diagnostics and any already-observed session ID; no automatic rerun is performed.

Commands such as `agent create-chat`, `agent --resume <id>` and `agent persist` exist, but this skill uses explicit IDs and headless print calls. Detached helper execution supplies SSH persistence without adding a server/framework or relying on interactive persistent-session UI.

Official references:

- [Cursor CLI modes](https://cursor.com/docs/cli/using)
- [Headless output contract](https://cursor.com/docs/cli/reference/output-format)
- [CLI permission tokens](https://cursor.com/docs/cli/reference/permissions)
- [Claude Opus 5.5](https://prod.cursor.com/docs/models/claude-opus-5-5)

Verified families: `claude-opus-5-5-{low,medium,high,xhigh,max}` (optionally `-fast`) and `gemini-4-argon-{low,medium,high}`. Gemini's real init label was `Gemini 4 Argon Medium`, with a successful terminal result. These labels are routing evidence from Cursor, not independent proof of the upstream provider's implementation. Verify the live account list on every consultation. Never change a saved job's exact model ID during a follow-up.

Local state root: `~/Library/Application Support/cursor-advisor/`. Local Cursor authentication and model availability are checked before each consultation. No NAS path, old skill compatibility entry, old-directory discovery, or credential copying is used.

Local verification on 2026-10-13: CLI `2026.10.01-e373342`, authenticated in authorized execution, and all four requested model IDs advertised by the live account list. Real synthetic reviews completed for `claude-opus-5-5-medium`, `gemini-4-argon-low`, `gemini-4-argon-medium`, and `gemini-4-argon-high`. Opus foreground continuation and Argon Medium detached continuation both preserved their saved model/session IDs. Explicit model change was rejected without CLI access or saved-state changes. All calls used `--sandbox enabled`, Ask mode and tool denies; no tools or source/workspace mutations were observed. Codex discovered the new user skill and no old skill entry. The restricted Codex execution sandbox could not observe local authentication; authorized execution could. This is separate from Cursor's own enabled sandbox.
