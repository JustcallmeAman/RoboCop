<!--
Sync Impact Report
===================
Version change: 0.0.0 → 1.0.0
MAJOR bump rationale: Initial constitution ratification — all principles new.

Modified principles: N/A (initial version)

Added sections:
  - Core Principles (5): Resource Efficiency, On-Device Processing,
    Safety Gates, Modular Architecture, Simplicity
  - Hardware Constraints
  - Development Workflow & Quality Gates
  - Governance

Removed sections: N/A

Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ compatible (Constitution Check
    section is generic, will be populated per-plan)
  - .specify/templates/spec-template.md — ✅ compatible (no constitution-
    specific references)
  - .specify/templates/tasks-template.md — ✅ compatible (task phases are
    generic)

Follow-up TODOs: None
-->

# RoboCop Constitution

## Core Principles

### I. Resource Efficiency

The Jetson Orin Nano Super has 8GB of unified memory shared between
CPU and GPU. This is the hardest constraint in the system.

- Every module MUST document its peak memory footprint before merge.
- GPU memory is reserved for inference workloads (LLM, vision models).
  CPU-bound tasks (audio capture, TTS playback, HTTP serving) MUST NOT
  allocate GPU memory.
- New model additions MUST include a memory budget showing total system
  usage stays below 7GB (1GB reserved for OS and headroom).
- When two approaches exist, prefer the one that uses less memory, even
  if the alternative is marginally faster. Latency is secondary to
  fitting in memory.
- Quantized models (int8, Q4_K) are the default. Full-precision weights
  require explicit justification.

### II. On-Device Processing

All core functionality MUST run locally on the Jetson without network
access. The system operates as a fully offline companion.

- Speech recognition, LLM inference, TTS, and vision MUST function
  without internet connectivity.
- Cloud services (Claude API, weather APIs, Uber API) are optional
  enhancements, never dependencies for core operation.
- No telemetry, analytics, or data transmission unless the user
  explicitly initiates it.
- The public GitHub repo MUST NOT contain secrets, API keys, tokens,
  or credentials. All secrets go in `.env` files excluded by
  `.gitignore`.

### III. Safety Gates

Life-safety decisions use deterministic rules, never LLM inference.
Layer 1 (Rules Engine) overrides all other layers.

- Biomarker thresholds (heart rate spikes, sustained elevated HR)
  trigger deterministic responses — no LLM involved.
- Intoxication detection (GPS + time + HR compound triggers) uses
  hard-coded logic with fixed thresholds.
- The rules engine MUST NOT be bypassed, disabled, or overridden by
  any other system component.
- Emergency responses (call for help, Uber suggestion) fire
  immediately without waiting for LLM reasoning.

### IV. Modular Architecture

Each subsystem is a self-contained Python module with a clear
interface. Modules MUST be independently testable.

- The canonical modules are: `config`, `llm`, `stt`, `tts`, `vision`,
  `memory`, `reasoning`, `agent_loop`.
- A module MUST NOT import from another module's internals. Use the
  public interface defined at the module level.
- `agent_loop.py` is the only orchestrator. It composes modules but
  contains no domain logic itself.
- New modules follow the same pattern: single `.py` file in `src/`,
  init function, clean shutdown, documented public interface.
- If a module fails to initialize (e.g., camera not connected), the
  system MUST degrade gracefully — log the failure and continue
  without that capability.

### V. Simplicity

Start with the simplest implementation that works. Optimize only when
measured. YAGNI applies to everything.

- No abstractions until the third concrete use case. Three similar
  lines of code are better than a premature helper.
- No config files for values that change less than once a month —
  use constants.
- Prefer a single Python file per module over package directories
  until the file exceeds ~300 lines.
- Comments explain WHY, not WHAT. Well-named functions and variables
  are the documentation.
- Maximum response length is 1-3 sentences. The AI whispers, it does
  not lecture.

## Hardware Constraints

These constraints are derived from the physical hardware and MUST be
respected by all code running on the Jetson.

| Resource | Limit | Notes |
|---|---|---|
| Total RAM | 8GB unified (CPU + GPU) | OS baseline ~800MB headless |
| GPU memory budget | ~3GB for models | LLM (~1.9GB) + vision (~0.5GB) + headroom |
| CPU cores | 6x ARM Cortex-A78AE | Audio capture and TTS run here |
| Storage (NVMe) | 238GB, 1691 MB/s read | Primary for all workloads |
| Storage (MicroSD) | 256GB, 80 MB/s read | Boot chain only |
| MyriadX (OAK-D Lite) | 4 TOPS | On-camera inference, zero Jetson cost |
| Thermal | Passive + fan | Monitor via `tegrastats`, throttle at 80C |

- Audio capture (ReSpeaker XVF3800) uses ALSA direct, not PulseAudio,
  to minimize latency and CPU overhead.
- Bluetooth audio (Shokz) routes through PipeWire in HFP mode (16kHz
  mono). A2DP is preferred when stable.
- OAK-D Lite runs MobileNet SSD on its own MyriadX chip. Vision
  inference MUST stay on-camera unless a model requires Jetson GPU.
- New peripherals MUST work over USB or Bluetooth. No custom PCBs or
  kernel modules without explicit justification.

## Development Workflow & Quality Gates

### Workflow

1. **Develop on Mac** — edit code in the local repo at
   `/Users/amanzel/Development/RoboCop`.
2. **Deploy to Jetson** — push to GitHub, pull on Jetson via SSH
   (`ssh z@z-desktop.local`), or `scp` files directly.
3. **Test on hardware** — all sensor-dependent code MUST be tested on
   the actual Jetson with real peripherals connected.
4. **Commit from Mac** — git history lives in the Mac repo. Jetson is
   a deployment target, not a development environment.

### Quality Gates

Before merging any feature:

- [ ] **Memory check**: Run `tegrastats` during operation and confirm
      total usage stays under 7GB.
- [ ] **Graceful degradation**: Disconnect each peripheral one at a
      time and verify the system continues without crashing.
- [ ] **Response latency**: End-to-end loop (mic → transcribe → LLM →
      TTS → speaker) completes within 5 seconds.
- [ ] **Cold start**: System initializes all modules and is ready to
      accept speech within 30 seconds of launch.
- [ ] **No secrets**: `git diff` shows no API keys, tokens, passwords,
      or credentials.

### Python Standards

- Python 3.10 (Jetson JetPack 6.2.1 default).
- No type checkers or linters enforced yet — code MUST be readable
  and follow the module pattern in Principle IV.
- `requirements.txt` for pip dependencies. Pin versions for
  reproducibility on ARM64.

## Governance

This constitution is the highest-authority document for the RoboCop
project. It supersedes README guidance, inline comments, and verbal
agreements when conflicts arise.

- **Amendments** require updating this file with a version bump,
  documenting the change in the Sync Impact Report comment block,
  and propagating changes to dependent templates.
- **Version scheme**: MAJOR.MINOR.PATCH — MAJOR for principle
  removals or redefinitions, MINOR for new principles or sections,
  PATCH for clarifications and wording.
- **Compliance**: Every spec, plan, and task list produced by the
  speckit workflow MUST reference this constitution. The plan
  template's "Constitution Check" section enforces this.
- **Disputes**: When a technical decision conflicts with a principle,
  the principle wins unless a Complexity Tracking entry in the plan
  explicitly justifies the exception.

**Version**: 1.0.0 | **Ratified**: 2026-05-16 | **Last Amended**: 2026-05-16
