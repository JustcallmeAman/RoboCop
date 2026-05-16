<!--
Sync Impact Report
===================
Version change: 1.0.0 → 2.0.0
MAJOR bump rationale: All principles redefined. Expanded from 5 to 6
principles with materially different scope, added concrete latency
targets, type hint requirements, and documentation standards.

Modified principles:
  - "I. Resource Efficiency" → "I. Real-Time Performance"
    (narrowed from general memory budgets to concrete latency/FPS
    targets; memory budgets moved to Principle II)
  - "II. On-Device Processing" → "II. Hardware Constraint Awareness"
    (expanded to include thermal, power, and edge-first processing;
    secrets policy moved to Governance)
  - "III. Safety Gates" → "IV. Safety & Graceful Degradation"
    (broadened from rules-engine-only to full fault tolerance across
    all modules)
  - "IV. Modular Architecture" → "III. Modular Software Architecture"
    (added fault isolation and sensor pipeline independence)
  - "V. Simplicity" → removed as standalone principle (YAGNI guidance
    absorbed into Code Quality Standards)

Added sections:
  - Principle V: Code Quality Standards (type hints, abstract sensor
    APIs, linting)
  - Principle VI: Documentation Standards (wiring diagrams, calibration
    procedures)

Removed sections:
  - "Hardware Constraints" table (absorbed into Principle II)
  - "Python Standards" subsection (absorbed into Principle V)

Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ compatible (Constitution
    Check section is generic, populated per-plan)
  - .specify/templates/spec-template.md — ✅ compatible (no
    constitution-specific references)
  - .specify/templates/tasks-template.md — ✅ compatible (task phases
    are generic)

Follow-up TODOs: None
-->

# RoboCop Constitution

## Core Principles

### I. Real-Time Performance

The system is a wearable companion that responds in real time. Latency
and throughput targets are non-negotiable for a usable experience.

- End-to-end voice loop (mic capture → STT → LLM → TTS → speaker)
  MUST complete within 5 seconds p95.
- Speech-to-text (faster-whisper) MUST return transcription within
  1.5 seconds of utterance end.
- LLM inference (Ollama/qwen2.5:3b) MUST produce first token within
  800ms and complete within 3 seconds for a typical 1-3 sentence
  response.
- Vision pipeline (OAK-D Lite object detection) MUST sustain a
  minimum of 15 FPS for scene context. Dropping below 10 FPS for
  more than 2 seconds MUST trigger a warning log.
- TTS synthesis (Piper) MUST produce audio within 500ms of receiving
  text.
- All latency targets MUST be measured on the Jetson under load
  (LLM + vision + audio running simultaneously), not in isolation.
- If a latency target cannot be met, the module MUST log a
  `PERF_DEGRADED` event with measured vs. target values.

### II. Hardware Constraint Awareness

The Jetson Orin Nano Super has 8GB unified memory, 6 ARM cores,
1024 CUDA cores, and passive+fan cooling. Every decision respects
these physical limits.

**Memory Budget**:
- Total system usage MUST stay below 7GB (1GB reserved for OS).
- GPU memory is reserved for inference: LLM (~1.9GB) + vision
  (~0.5GB) + headroom. CPU-bound tasks (audio capture, TTS playback,
  HTTP serving) MUST NOT allocate GPU memory.
- New model additions MUST include a memory budget showing the
  allocation fits. Quantized models (int8, Q4_K) are the default;
  full-precision weights require explicit justification.

**Thermal Management**:
- Code MUST NOT disable or override the fan controller.
- If `tegrastats` reports SOC temperature above 80C, the system
  MUST reduce inference frequency (skip vision frames, increase
  polling intervals) until temperature drops below 75C.
- Long-running benchmarks or stress tests MUST monitor temperature
  and abort if sustained above 85C.

**Power Budget**:
- The system runs on a 140W charger in MAXN_SUPER power mode.
- Battery-powered operation is not supported yet. When it is added,
  a power-profile system MUST allow trading latency for lower power
  draw.

**Edge-First Processing**:
- All core functions (STT, LLM, TTS, vision, rules engine) MUST
  operate fully offline with no network dependency.
- Cloud services (Claude API, weather, Uber, Google Places) are
  optional enhancements. The system MUST function identically when
  disconnected from the internet.
- OAK-D Lite runs inference on its MyriadX chip (4 TOPS). Vision
  models MUST stay on-camera unless they specifically require Jetson
  GPU.
- New peripherals MUST work over USB or Bluetooth. No custom PCBs or
  kernel modules without explicit justification.

### III. Modular Software Architecture

Each sensor pipeline is a self-contained Python module with a defined
interface. Modules MUST be independently testable and fault-tolerant.

- The canonical modules are: `config`, `llm`, `stt`, `tts`, `vision`,
  `memory`, `reasoning`, `wakeword`, `agent_loop`.
- Each module MUST expose: an `init()` function, a `shutdown()`
  function, and a clearly defined public API. Internal helpers MUST
  be prefixed with `_`.
- A module MUST NOT import from another module's internals. Cross-
  module communication goes through the public interface only.
- `agent_loop.py` is the sole orchestrator. It composes modules but
  contains no domain logic — no STT processing, no LLM prompt
  construction, no audio encoding.
- Each sensor pipeline (audio, vision, biometrics) MUST be testable
  in isolation with mock inputs. A vision module test MUST NOT
  require a connected microphone; an STT test MUST NOT require a
  connected camera.
- New modules follow the pattern: single `.py` file in `src/`,
  `init()`/`shutdown()` pair, type-hinted public interface. Grow to
  a package directory only when the file exceeds ~300 lines.

### IV. Safety & Graceful Degradation

The system MUST remain operational when any single module fails. No
single peripheral failure may crash the system or produce unsafe
behavior.

**Module Fault Tolerance**:
- If a module fails to initialize (camera disconnected, mic
  unplugged, Bluetooth dropped), the system MUST log the failure
  and continue without that capability.
- The agent loop MUST track which modules are active and adjust its
  behavior accordingly (e.g., skip vision context when camera is
  unavailable, fall back to text-only when TTS fails).
- A module that crashes at runtime MUST be caught by the orchestrator.
  The crash MUST be logged with a full traceback. The system MUST NOT
  exit.

**Life-Safety Rules Engine**:
- Life-safety decisions (biomarker thresholds, intoxication detection,
  emergency triggers) use deterministic rules in Layer 1, never LLM
  inference.
- The rules engine MUST NOT be bypassed, disabled, or overridden by
  any other component.
- Emergency responses (Uber suggestion, grounding techniques, call for
  help) fire immediately without waiting for LLM reasoning.
- Compound triggers (GPS + time + HR) use hard-coded logic with fixed,
  documented thresholds.

**Secrets & Public Repo Safety**:
- The GitHub repo is public. It MUST NOT contain API keys, tokens,
  passwords, or credentials at any point in git history.
- All secrets go in `.env` files excluded by `.gitignore`.
- No telemetry, analytics, or data transmission unless the user
  explicitly initiates it.

### V. Code Quality Standards

Python is the primary language. Code MUST be readable, typed, and
structured around clean sensor abstractions.

- **Python 3.10** (JetPack 6.2.1 default). All code MUST run on
  this version.
- **Type hints are required** on all public function signatures
  (parameters and return types). Private helpers SHOULD have type
  hints but are not blocked on them.
- Every sensor interface (microphone, camera, Bluetooth audio,
  biometrics, GPS) MUST be abstracted behind a clean API class or
  module. Callers interact with the abstraction, never with raw
  hardware handles (ALSA device strings, DepthAI pipeline objects,
  BlueZ D-Bus calls).
- `requirements.txt` for pip dependencies. Pin exact versions for
  ARM64 reproducibility.
- No premature abstractions. Three similar lines are better than a
  helper nobody reuses. Extract only on the third concrete use case.
- Comments explain WHY, not WHAT. Well-named functions are the
  documentation for behavior.
- Maximum AI response length: 1-3 sentences. The companion whispers,
  it does not lecture.

### VI. Documentation Standards

Every module that interfaces with hardware MUST include documentation
linking to physical setup and calibration.

- Each hardware-facing module MUST reference a wiring diagram or
  connection guide. This can be:
  - A section in the module's docstring pointing to `hardware/jetson/`
    setup scripts.
  - A `# Hardware: see hardware/jetson/<script>.sh` comment at the
    top of the file.
  - A dedicated `docs/hardware/<module>.md` file for complex setups.
- Each sensor module MUST document its calibration procedure:
  - **Microphone (ReSpeaker)**: How to verify capture levels, test
    beamforming, check for silence (USB re-init).
  - **Camera (OAK-D Lite)**: How to verify detection model is loaded,
    confirm FPS, check stereo alignment.
  - **Audio output (Shokz)**: How to verify Bluetooth connection,
    test playback, confirm PipeWire routing.
  - **Biometrics (Polar H10)**: How to pair, verify HR stream, check
    signal quality. *(Future — document when integrated.)*
  - **GPS**: How to get a fix, verify coordinates, test geofencing.
    *(Future — document when integrated.)*
- Setup scripts in `hardware/jetson/` MUST explain what each command
  does and why, not just list commands.
- README.md remains the high-level overview. Module-specific hardware
  details live alongside the code or in `docs/hardware/`.

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
- [ ] **Thermal check**: Run for 5+ minutes under load; SOC temp MUST
      stay below 80C sustained.
- [ ] **Graceful degradation**: Disconnect each peripheral one at a
      time and verify the system continues without crashing.
- [ ] **Response latency**: End-to-end voice loop completes within
      5 seconds p95.
- [ ] **Vision FPS**: Object detection sustains 15+ FPS under load.
- [ ] **Cold start**: System initializes all modules and is ready to
      accept speech within 30 seconds of launch.
- [ ] **Type check**: All public functions have type hints on
      parameters and return values.
- [ ] **Hardware docs**: New sensor modules reference wiring/setup
      guide and document calibration procedure.
- [ ] **No secrets**: `git diff` shows no API keys, tokens, passwords,
      or credentials.

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

**Version**: 2.0.0 | **Ratified**: 2026-05-16 | **Last Amended**: 2026-05-16
