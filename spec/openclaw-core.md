# OpenClaw core — spec

Belongs to Window C (router-local-models), which now owns MattGPT's agent shell, not just the local model layer.

## Decision

Build on OpenClaw's **core runtime** (memory system, skill execution, multi-provider model abstraction) under strict hardening. This reverses the earlier "read as reference only" call — see `.claude/team-status.md` for the full reasoning trail. The decision was made with the security history known, not despite not knowing it.

## Why this is judged acceptable

OpenClaw has a real CVE history (CVE-2026-25253 and others). Investigation showed most of the chain (CVE-2026-44112/-44113/-44115) requires an initial foothold via a malicious third-party plugin or prompt injection from untrusted content — they're escalation bugs, not independent entry points. CVE-2026-44118's remote exploitability depends on the gateway accepting external connections. The four hardening steps below close off every precondition that's within our control.

## Install

macOS/Linux/WSL2:
```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```
Windows PowerShell:
```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```
Or via npm (Node 24.16+/26.1+):
```bash
npm install -g openclaw@latest --allow-scripts=openclaw
```
Then:
```bash
openclaw onboard --install-daemon
openclaw gateway status
openclaw dashboard
```

## Required hardening — non-negotiable, not optional setup steps

1. **Gateway bound to `127.0.0.1` only, never `0.0.0.0`.** This is the one that matters most — it makes the gateway unreachable from outside the machine, which directly closes CVE-2026-44118's precondition.
2. **Decline every messaging integration** during onboarding (WhatsApp/Telegram/Slack/Discord). MattGPT has no use for any of them, and they're the exact surface that's been exploited at scale elsewhere.
3. **Decline all ClawHub skill/extension installs.** Only OpenClaw's built-in functionality — no third-party marketplace code runs inside MattGPT. This closes the "malicious plugin" foothold explicitly named in the CVE chain.
4. **Disable telemetry** — `update.checkOnStart: false` in config.
5. **Treat all external content the agent reads as data, not instructions** — calendar event text, any web content, any self-logged note. This is the one precondition hardening config alone can't close (prompt injection is the other listed foothold in the CVE chain) — it has to be enforced in how MattGPT's own code handles untrusted text, not just in OpenClaw's settings.

## Ongoing obligation, not a one-time setup

Stay on the latest patched OpenClaw release. This entire risk assessment assumes patches keep landing — an unpatched, aging install is a different risk posture than what was evaluated here.

## Dependency mode

Depend (not fork) — per `CLAUDE.md`'s build-philosophy table, now updated to reflect this decision.

## Verification (Window C, install + hardening)

Before installing, I checked the actual advisories behind the CVEs cited above. Two corrections to the reasoning in "Why this is judged acceptable": CVE-2026-25253's token-theft RCE is browser-pivoted — a user logged into the Control UI who visits a malicious page leaks their gateway token regardless of loopback binding, per the GitHub Security Advisory (GHSA-g8p2-7wf7-98mq) and multiple vendor writeups. And CVE-2026-44118 is a flaw *in* the loopback MCP gateway itself (a local process with a stolen bearer token escalates to owner), not something loopback-binding closes. Matthew reviewed this and chose to proceed with the install as specified regardless.

Installed OpenClaw **2026.9.6** — past the patched versions for all six CVEs discussed here (2026.1.29 for CVE-2026-25253; before 2026.4.22 for the Claw Chain CVEs), so this install isn't exposed to those specific disclosed bugs. Onboarded non-interactively (`openclaw onboard --non-interactive --accept-risk --auth-choice ollama --gateway-bind loopback --gateway-auth token --secret-input-mode ref --install-daemon --skip-channels --skip-skills --skip-ui`) so the 5 hardening steps are enforced by flag rather than by clicking through a wizard:

1. **Gateway bind = loopback.** Confirmed via `openclaw gateway status` ("Gateway: bind=loopback (127.0.0.1)... Loopback-only gateway; only local clients can connect") and directly in `~/.openclaw/openclaw.json` (`gateway.bind: "loopback"`). `openclaw security audit` reports 0 critical findings.
2. **No messaging integrations.** `--skip-channels` — `openclaw channels status` confirms "no configured chat channels."
3. **No ClawHub skills/extensions installed.** `--skip-skills` — `openclaw skills list` shows only `openclaw-bundled`/`openclaw-custodian`/`openclaw-extra` (shipped-in-the-box) skills; nothing installed via ClawHub. The config has no `clawhub` entry.
4. **Telemetry disabled.** `openclaw telemetry off` → config shows `telemetry.enabled: false`. Also explicitly set `update.checkOnStart: false` (the exact key this spec names) and confirmed via `openclaw config get update.checkOnStart` → `false`.
5. **Untrusted content as data, not instructions.** No MattGPT-OpenClaw integration code exists yet, so this is a design commitment for whoever writes it: calendar event text, web content, and self-logged notes that reach the agent must be passed as inert data in tool/function results, never concatenated into the system or developer prompt as if they were instructions from Matthew. This is the precondition hardening config can't close (per this spec's own §5) — the CVE-2026-25253 write-ups above are one concrete illustration of why that boundary matters: a link is content, not a command.

**Extra precaution beyond this spec:** passed `--skip-ui`, so the Control UI/dashboard was never opened as part of setup. Its route still exists on the loopback gateway (`http://127.0.0.1:18789/`), so the browser-pivoted CVE-2026-25253 vector isn't structurally impossible — but the operational rule going forward is: never open that dashboard in a browser also used for general browsing, since that's the actual attack surface, and loopback binding alone doesn't remove it.
