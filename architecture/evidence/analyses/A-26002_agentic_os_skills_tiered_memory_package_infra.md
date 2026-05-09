
---
title: Agentic OS, Tiered Cognitive Memory, and Package-Driven Infrastructure
date: 2026-03-07
tags:
- architecture
- context_management
- devops
options:
  token_size: 6595
  id: A-26002
  status: active
  sources:
  - S-26001
  produces: []
  type: analysis
  version: 1.0.0
  birth: '2026-03-07'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: These architectural patterns emerged from a concrete production challenge
  — building "Mentor Generator," a spoke repository in the ecosystem ({term}`ADR-26020`).
---
# A-26002: Agentic OS, Tiered Cognitive Memory, and Package-Driven Infrastructure

## Problem Statement

### The Catalyst: Mentor Generator

These architectural patterns emerged from a concrete production challenge — building "Mentor Generator," a spoke repository in the ecosystem ({term}`ADR-26020`). Mentor Generator is an AI-powered system that creates personalized learning courses: it interviews a user about their goals and background, researches contemporary sources on the chosen topic, assembles a structured curriculum with a teaching persona (tone, Socratic questioning style, strictness level), and then conducts an interactive learning session.

During the v0.31.0 overhaul of Mentor Generator, three systemic failures became impossible to ignore. These are not Mentor-specific — they apply to any agent that must combine domain expertise with structured output generation. Mentor Generator simply made them undeniable because the agent had to simultaneously be an interviewer, a researcher, a curriculum designer, and a teacher — all from a single system prompt.

### The Three Compounding Problems

1. **Cognitive Overload.** The Mentor Generator's system prompt grew to encode persona rules, pedagogical strategies, curriculum structure, Socratic questioning protocols, and YAML template constraints — all in one monolithic block. As the prompt grew, the model started ignoring rules at the bottom ("Instruction Drift"). Creative outputs degraded: the agent produced high-quality personas but low-quality curricula (or vice versa) because it could not attend to both simultaneously. This is the "One-Shot Fragility" problem: a single LLM call filling 10+ labeled sections causes attention to "smear" across competing concerns.

2. **Context Tax.** Reference data (the subject's documentation, foundational textbooks, research papers, student history) competes for the same finite context window as procedural logic. Injecting a 500-page biology textbook alongside a 30-line YAML mentor template guarantees that the template instructions will be diluted. The ~90K-token "performance cliff" means that stuffing everything into context is not just inefficient — it actively degrades output quality.

3. **Distribution Friction.** In the Hub-and-Spoke ecosystem ({term}`ADR-26020`), Mentor Generator is one spoke among several (vadocs for validation, a future Skills Library). Sharing domain expertise — pedagogical strategies, validation rules, research protocols — across these repos requires manual copy-paste of prompts, scripts, and validation logic. There is no versioned, testable, installable unit of "expertise."

These three problems are interconnected: solving one without the others produces sophisticated workarounds, not production systems. The Gemini dialogue (S-26001) explored all three through the lens of Mentor Generator and converged on an integrated architectural response applicable to any production-grade agent.

### Three Distinct Failure Modes

The dialogue distinguishes between three related but distinct degradation patterns, each requiring different mitigations:

| Failure Mode | Mechanism | When It Occurs |
|---|---|---|
| **Instruction Drift** | Gradual degradation over conversation turns — the model "forgets" earlier rules as new context accumulates | Long multi-turn sessions (100+ turns) |
| **Prompt Fatigue** | Model ignores rules at the bottom of a long prompt — attention distribution is uneven within a single system message | Long system prompts (200+ lines) |
| **Lost in the Middle** | Information in the middle of the context window gets less attention than content at the beginning or end | Large context windows with mixed content types |

The Skills architecture addresses all three: Progressive Disclosure prevents Prompt Fatigue (only relevant skills are loaded), tag-filtered startup prevents Lost in the Middle (less total content), and re-injection of skill instructions at tool-call boundaries prevents Instruction Drift.

## Key Insights

### 1. The Honest Assessment: Skills Are Not a Silver Bullet

The dialogue begins with a critical acknowledgment: at the end of the day, a Skill is still a prompt, and it is "absolutely susceptible to Instruction Drift." The formulation is explicit: "It isn't a silver bullet. It is still Prompt Engineering. You are essentially trading 'Management Overhead' (manually pasting prompts) for 'Architecture Overhead' (organizing .md files)."

What transforms Skills from "a sophisticated workaround" into a production tool is not the `.md` file itself, but the combination of:
- **Executable code** (scripts replace instructions with deterministic logic)
- **Progressive disclosure** (protect context window)
- **Constraints over instructions** ("The Template as Jail" — see below)
- **Validation tooling** (vadocs enforces structural compliance)

Without these four reinforcements, Skills regress to "Vibe-based Engineering."

### 2. The Agentic OS Paradigm — Model as Processor, Agent as OS, Skills as Apps

The central metaphor, validated by the Claude Skills inventors (Barry Zhang, Mahesh Murag), maps the AI agent stack to computing history:

| Computing Layer | AI Agent Layer | Role |
|---|---|---|
| Processor (CPU) | LLM (Model) | Raw intelligence — stateless, general-purpose, expensive to build |
| Operating System | Agent Runtime | Orchestrates context window, file system, MCP connections, tool execution |
| Applications | Skills | Domain expertise — portable, versioned, composable folders |

The inventors use a powerful framing: "Who do you want doing your taxes? The 300 IQ mathematical genius, or the experienced tax professional? Agents today are like the genius — brilliant but lacking expertise." Skills provide that expertise.

**Critical distinction from naive "Skills as .md files":** The Claude Skills inventors explicitly describe Skills as **atomic suites** containing:
- `SKILL.md` — metadata + core instructions (the "entry point")
- `/scripts` — executable Python/Bash logic, pre-verified tools
- `/tests` — golden-file fixtures that verify the skill's logic with zero API calls
- `/assets` — templates, schemas, reference data
- Potentially binaries and compiled executables

This is software engineering, not prompt engineering. A Skill is closer to a `.deb` package than a system prompt snippet. The inclusion of `/tests` as a first-class component means the skill contract is verifiable — aligning with the project's TDD philosophy.

**"Template as Jail":** The core design philosophy of "Predictability comes from constraints, not instructions" ({term}`ADR-26023`) manifests concretely in Mentor Generator: instead of telling the LLM "be a good teacher," we force it to fill a strictly validated 30-line YAML template. The template acts as the hardware spec of the Agentic OS — the model cannot produce output that violates the schema, regardless of Instruction Drift.

**Progressive Disclosure** protects the context window:
- **Level 1 (Discovery):** Only the YAML frontmatter (name, description, tags) is shown — ~50 tokens per Skill
- **Level 2 (Activation):** The full `SKILL.md` body is loaded when the agent decides the Skill is relevant
- **Level 3 (Execution):** Associated scripts and assets are read/run only when the task requires them

This means an agent can "know about" 1,000 skills at ~50K tokens (Level 1), while only ever loading 2-3 full skills into context for a given task.

**Skills as Slash Commands:** Skills double as invocable commands. If a file is named `.claude/skills/refactor.md`, the user can type `/refactor` and the agent immediately loads that skill as its "mission." This provides a command-based activation path alongside the tag-based discovery.

**Skills + MCP Complementarity:** The transcript establishes a specific architectural relationship: "MCP is providing the connection to the outside world while skills are providing the expertise." Skills can orchestrate workflows of multiple MCP tools stitched together — MCP handles connectivity, Skills handle the logic.

**Continuous Learning — Agent-Authored Skills:** The Skills inventors describe a compounding knowledge base: "Anything that Claude writes down can be used efficiently by a future version of itself." The agent can create, update, and deprecate its own skills. "Claude on day 30 of working with you is going to be a lot better than Claude on day 1." This means skill folders must be designed as writable and versioned, not read-only.

**Non-Technical Skill Builders:** The transcript highlights early validation that "skills are being built by people that aren't technical — people in finance, recruiting, accounting, legal." This changes the audience model for the skills ecosystem: skill authoring must be accessible beyond engineering teams, which has implications for tooling, documentation, and validation complexity.

### 3. Three-Tier Knowledge Model — Skills, Context, RAG

The dialogue refined the simple Skills-vs-RAG binary into a three-layer knowledge model:

| Tier | Name | Knowledge Type | Examples in Mentor Generator |
|---|---|---|---|
| **Tier 1: Skills** | "The How" (Procedural) | Logic, validation rules, workflow steps, executable scripts | Pedagogical strategies, Socratic questioning protocols, feedback loops |
| **Tier 2: Projects/Context** | "The What" (Grounding State) | Project-specific data that the OS manages — current curriculum, student records, session state | `student_state.json`, `curriculum_graph.json`, the active lesson plan |
| **Tier 3: RAG** | "The Library" (Declarative) | Documentation, specs, research papers, historical logs — vast, unstructured reference material | Biology textbooks, API docs, research papers, Slack history |

The critical addition is **Tier 2: Projects/Context** — grounding data that is neither procedural knowledge nor encyclopedic reference. This is the "state" that the OS manages, kept distinct from both logic (Skills) and reference (RAG) to avoid cognitive overload.

**The Rule of Thumb:** If it is a recipe, make it a Skill. If it is current session state, manage it as Context. If it is an encyclopedia, put it in RAG.

**Delivery mechanisms differ per tier:**

| Tier | Delivery | Reliability |
|---|---|---|
| Skills | Filtered by tags at startup, progressively disclosed into context | Deterministic — core logic is always present or explicitly loaded |
| Context | Assembled per-turn by the orchestrator from persistent storage | Deterministic — code-managed, not LLM-managed |
| RAG | Just-In-Time (JIT) retrieval via tool-calling only when relevant | Probabilistic — vector search may return wrong chunk |

**Why not "Pure RAG for Everything"?** Vector search is probabilistic. The agent might retrieve the wrong "how-to" step, leading to catastrophic failure in structured tasks like YAML generation or validation. Procedural knowledge must be deterministic.

**Why not "Pure Skills (No RAG)"?** Violates the ~90K-token "performance cliff" for many models. Historical logs, large specs, and research papers must remain external.

**Alignment with existing ADRs:**
- {term}`ADR-26030` (Stateless JIT Context Injection) governs how declarative knowledge enters the context
- {term}`ADR-26013` (Just-in-Time Prompt Transformation) established the JIT pattern; this analysis extends it to the Skill/RAG boundary

### 4. Tag-Filtered Skill Discovery and the `activate_skill` Tool Interface

If an organization has 1,000 skills, loading all 1,000 Level 1 descriptions (~50K tokens) before the user speaks is wasteful. The solution: **tag-based filtering at startup**.

Each `SKILL.md` frontmatter includes a `tags` field (e.g., `[generator, discovery, academic]`). When an agent initializes, it receives a "Capability Filter" (e.g., `capabilities: ["generator", "pydantic-logic"]`) and only registers skills matching those tags.

**The Boot Sequence:**
1. Code scans the skills directory, reads YAML frontmatter only
2. Filters by tags matching the agent's declared capabilities
3. Injects only matching skill descriptions into the system prompt (Level 1)
4. Attaches a `search_docs` tool connecting to the RAG vector store (for declarative knowledge)
5. Agent runs — loads full skill content on demand (Level 2/3 for procedural knowledge)

**The `activate_skill(name)` Tool Interface:** The boundary between Level 1 (passive awareness) and Level 2 (active loading) is implemented as a tool call. The system prompt tells the LLM:

> "You have access to the following skills. If a task requires one, call the `activate_skill(name)` tool: **researcher** — Deep web analysis and source verification; **yaml-validator** — Ensures mentor configs follow strict schemas."

When the LLM calls `activate_skill("researcher")`, the runtime reads the full `SKILL.md` body and injects it into the conversation. This keeps the activation deterministic and auditable.

**Reference implementation** of the skill indexer using `python-frontmatter`:

```python
import frontmatter
from pathlib import Path

def index_skills(skills_dir: str):
    skill_registry = []
    for skill_path in Path(skills_dir).rglob("SKILL.md"):
        with open(skill_path) as f:
            post = frontmatter.load(f)
        skill_registry.append({
            "name": post["name"],
            "description": post["description"],
            "path": str(skill_path.parent)
        })
    return skill_registry
```

**vadocs Validation Rules for Skill Frontmatter:**
- **FM01:** `name` and `description` must exist in frontmatter
- **FM02:** `name` must match the folder name
- **FM03:** `description` must be under 1,024 characters (to save tokens during Level 1 discovery)

These bridge the conceptual architecture to the project's existing vadocs toolchain.

### 5. Package-Driven "Virtual Monorepo" Infrastructure

The dialogue explored three distribution models for sharing expertise across repos:

| Model | Mechanism | Strengths | Weaknesses |
|---|---|---|---|
| Git-based Registry | `git clone` skills repo into `.claude/skills/` | Visible, editable, agent can write back | Manual setup, no dependency management |
| PyPI Package | `uv add my-org-skills` | Versioned, immutable, single `uv sync` setup | Opaque (buried in site-packages), static |
| **Dogfooded PyPI via uv Workspace** | `uv sync` with workspace members | Versioned + visible + validated via vadocs | Workspace config complexity |

**The winner: Dogfooded PyPI via `uv` Workspaces.** This combines:
- **PyPI distribution** — a new developer runs `uv sync`, no manual setup
- **Workspace linking** — during development, changes to `vadocs` or `skills` are immediately visible to `mentor_generator`
- **Dogfooding** — vadocs validates skill structure (frontmatter, required scripts, naming conventions) as a pre-commit hook, exactly the same way it validates ADRs

```toml
# pyproject.toml (Ecosystem Root)
[tool.uv.workspace]
members = ["agent", "skills", "vadocs"]

[tool.uv.sources]
my-org-skills = { workspace = true }
vadocs = { workspace = true }
```

**Rejected alternatives:**
- **Git Submodules:** High "Maintenance Tax" — notoriously difficult to keep in sync, "Detached HEAD" states
- **Traditional Monorepo:** Violates Hub-and-Spoke model, prevents independent versioning
- **Forking Template:** Divergence trap — a bug fix in core `llm_provider.py` must be merged into N forks. The fundamental principle: **composition over inheritance** applied to agent architecture. You don't fork the OS for each application; you compose capabilities via installable skills.

### 6. Builder/Runtime Separation — Two-Phase Agent Architecture

The dialogue converged on treating the complete system as a **compiler + virtual machine**:

**Generation Phase (The Builder/Compiler):**
```
User Intent → Interviewer Agent → User Profile JSON
                                            ↓
Web Sources → Researcher Agent → Research Dossier JSON  → Creative Engine → MENTOR PACKAGE
                                                           ↑
                                               YAML Templates
```

**Learning Phase (The Runtime/VM):**
```
MENTOR PACKAGE → Session Orchestrator ←→ Student State JSON
                         ↓
                 Context Assembler → LLM Inference → State Extractor → Student State JSON
                         ↑                                    ↓
                   User Learner ←──────────────────────────────┘
```

**The Mentor Package** is the "binary" — a directory containing:
- `personality.yml` — the "who" (tone, strictness, Socratic level)
- `research_dossier.json` — the "what" (verified facts/sources from the Researcher)
- `curriculum_graph.json` — the "path" (dependency map of concepts)
- `student_state.json` — the "record" (starts empty; tracks mastery and progress)

**Why this separation matters:**
- If the LLM halluccinates during a lesson, the Runtime cross-references the `research_dossier.json` and can flag the error before the user sees it
- You can swap the "Brain" (LLM) mid-course without losing progress — `student_state.json` is model-agnostic
- The LLM is treated as a **stateless function** — the Runtime manages all persistence

**The Multi-Agent Assembly Line:** To solve the One-Shot Fragility problem (a single LLM call producing 10+ sections), the Builder decomposes into specialized sub-agents:
- **Agent A (Persona):** Uses the user profile to generate name, tone, and mission
- **Agent B (Architect):** Takes the Persona + Profile and builds the Curriculum
- **Agent C (Reviewer):** Audits the output against the user's constraints (e.g., "Must fit 4GB RAM")

Each agent has a smaller signal-to-noise ratio, preventing the attention-smearing that degrades monolithic generation.

**The Structured Extraction Pattern:** Instead of the LLM returning labeled text blocks for post-hoc parsing, libraries like Instructor or Outlines force the LLM to output a Pydantic model directly at inference time. If the LLM misses a required section, the tool rejects the token and retries. This replaces "parsing" with "validation" at the inference layer — a fundamentally more deterministic approach.

### 7. Researcher Agent — Architecture and Risks

**The "Recency Trap" Risk:** Web search often returns high-SEO marketing content rather than foundational sources. The Researcher needs a mechanism to distinguish between a Medium article and a Technical Specification. Without this, the entire downstream pipeline (curriculum, teaching sessions) is built on unreliable data.

The dialogue proposed three approaches for the web research phase, each addressing this risk differently:

| Alternative | Mechanism | Key Advantage |
|---|---|---|
| **Adversarial (Verification-First)** | Two agents: Explorer finds sources, Critic finds contradictions. Outputs a "Verified Research Dossier" with `certainty_score` per concept | Mathematically lowers the chance of teaching outdated content by forcing the system to "argue with itself" |
| **Knowledge Graph (Structure-First)** | Researcher outputs a directed graph of concept dependencies with `prerequisites`, `complexity_level`, and `verified_source_url` per node | Creative Engine follows a literal map instead of guessing curriculum order |
| **JIT (Runtime-First)** | Researcher creates `search_indices.json` with URLs and queries per chapter; micro-research happens per-chapter during learning | Keeps context window lean — mentor only "knows" what current lesson requires |

The research output is saved as a JSON artifact (`research_dossier.json`) in the output directory, creating an audit trail. A user can verify the mentor's sources before starting the course, directly addressing the hallucination risk.

### 8. DSPy — Where It Fits and Where It Does Not

The dialogue evaluated DSPy (Stanford's declarative LLM programming framework) against the project's core philosophy: **"Predictability comes from constraints, not instructions."**

**How DSPy works under the hood:** DSPy treats prompt strings as learnable parameters. When you "compile," an optimizer (like MIPROv2) uses Bayesian search or Hill Climbing to swap instruction phrasings and few-shot examples in and out, measuring which combination scores highest against your metric function. The "weights" being optimized are not neural network parameters — they are the discrete text of the instructions and demonstrations. Most DSPy optimizers do not change the LLM's weights; they optimize the discrete prompt space.

Key mechanisms:
- **Teacher/Student pattern:** A high-end model generates "Golden Traces" (successful reasoning chains); a smaller deployment model uses those traces as few-shot examples
- **Assertion loop:** `dspy.Assert` wraps LLM calls in a `while` loop — if the output fails a linter/assertion, the error is sent back to the LLM to retry before the Python code even receives the result
- **Model portability:** Because you define a Signature (Input/Output contract) rather than a string, re-compiling for a different model produces optimized instructions for that model's specific behavior

**The user's critical challenge:** "This is not programming, it is still prompt engineering but in a pipeline." The rebuttal: it is prompt engineering in the same way that a SQL Query Planner is "database indexing" — you describe the *what*, and the system uses an algorithm to find the most efficient *how*.

| Component | Logic Type | Best Tool | Rationale |
|---|---|---|---|
| Interviewer | Sequential/CLI | Python + JSON | Fixed questions don't need optimization |
| Researcher | Exploratory | DSPy (potentially) | Handles unpredictable web data; assertion loops can enforce source quality |
| Creative Engine | Structural | Pydantic/Jinja2 | High-fidelity mapping to strict YAML schema |
| Learning Engine | State Machine | Python Logic | Predictability in state saves is paramount |

**The "Self-Optimizing Mentor" — a distinct DSPy application:** Beyond using DSPy for the Researcher, the dialogue proposed using it for *runtime optimization of the teaching style*: treating `mentor_system_prompt.yml` as learnable parameters that a Judge LLM scores after each session, with DSPy compiling improved versions. This transforms the project from a "Mentor Generator" to a "Mentor Optimizer" — a feedback loop where procedural knowledge improves over time.

**The "Escaped String Hell" risk in Pure JSON prompts:** Using pure JSON arrays for multi-line prompts (Plan A) is technically clean but human-hostile for editing — "you'll be staring at `\n` and comma-delimited lists for your most important creative assets." This influenced the recommendation toward YAML/Jinja2 templates over raw JSON for prompt storage.

### 9. Industry-Level Alternatives Landscape

The dialogue surveyed four industry-level techniques for solving instruction injection, positioning the Skills architecture within the broader ecosystem:

| Technique | Mechanism | Reliability | Key Trade-off |
|---|---|---|---|
| **Dynamic Prompt Management / Prompt CMS** (Agenta, Portkey, LangSmith) | Prompts stored in versioned database, decoupled from code. A/B testing and non-engineer editing (PMs, Legal) | Medium — still prompt-based | Governance gain: non-engineers can update instructions without code deploys |
| **DSPy Compiled Prompts** (Stanford) | Declarative Signatures compiled via Bayesian optimization over prompt space | High for probabilistic tasks | Opacity: hard to debug *why* a particular prompt version was chosen |
| **Agentic RAG for Instructions** | Vector search over a "Policy Store" to retrieve the 3 most relevant *rules* (not data) per turn | Medium — maximizes attention on relevant instructions | Distinct from data RAG: retrieves *logic*, not *facts*. Solves "Lost in the Middle" by injecting only relevant rules |
| **Constrained Decoding** (Guidance, Outlines) | Regex or CFG-based token masking at the inference layer. Physically prevents the model from generating tokens that violate rules | **Mathematically guaranteed** — a regex mask is a hard boundary, not a suggestion | Requires inference-layer access; not available via all API providers |

The Skills architecture occupies a unique position: it is the only approach that combines executable code, progressive disclosure, and package-based distribution. But for non-negotiable constraints (e.g., "never output an API key"), Constrained Decoding provides a reliability class that no prompt-based approach can match.

### 10. The Evolution from Prompt Engineering to Software Engineering

The dialogue traces a clear maturity progression:

```
Stage 1: System Prompt (monolithic text blob)
  ↓  fails via Instruction Drift
Stage 2: Instruction Files (.md conventions — Aider, CLAUDE.md)
  ↓  fails via Prompt Fatigue (AI ignores rules at the bottom)
Stage 3: Granular Skills (.claude/skills/ — modular, contextual, progressively disclosed)
  ↓  fails via non-determinism (still "just prompts")
Stage 4: Atomic Skill Suites (SKILL.md + /scripts + /tests + /assets)
  ↓  executable and testable, but no distribution mechanism
Stage 5: Skill Ecosystem (PyPI packages, vadocs validation, tag-filtered discovery, cross-org sharing)
```

Each stage solves the previous stage's primary failure mode. The key insight is that Skills are only production-ready at Stage 4+ — when they include executable code and tests, not just markdown instructions.

### 11. Prefixed Namespace System for Cross-Repo ADRs

To resolve "Ecosystem Documentation Debt" (overlapping ADR numbers between repos), the dialogue proposed:

| Prefix | Scope |
|---|---|
| `ECO-` | Ecosystem/Hub standards |
| `MNT-` | Mentor Generator implementation |
| `SKL-` | Skills Library definitions |
| `VAD-` | vadocs validation rules |

Format: `[PREFIX]-[YY][NNN]` (e.g., `ECO-27001`). The Hub `adr_index.md` serves as a "Super-Index" linking to spoke indices.

This is a governance proposal that needs its own ADR before adoption. It potentially supersedes the current flat `ADR-NNNNN` convention established in {term}`ADR-26016`.

## Approach Evaluation

### Skills-Only vs. RAG-Only vs. Hybrid (Three-Tier)

| Criterion | Skills-Only | RAG-Only | Hybrid (Skills + Context + RAG) |
|---|---|---|---|
| Procedural reliability | High | Low (probabilistic retrieval) | High (Skills handle procedures) |
| Knowledge scalability | Low (context limit) | High (millions of docs) | High (RAG handles volume) |
| Context efficiency | Medium (all skills loaded) | High (JIT chunks) | High (tag-filtered Skills + JIT RAG) |
| Determinism | High | Low | High for procedures, acceptable for reference |
| State management | None (stateless prompts) | None (search only) | Explicit (Context tier manages session state) |
| Implementation complexity | Low | Medium | Medium-High |

**Verdict:** The three-tier hybrid is the only viable production architecture. Skills-Only collapses at scale; RAG-Only is unreliable for procedural logic; two-tier (Skills + RAG) conflates session state with reference data.

### Package Distribution: PyPI vs. Git Clone vs. uv Workspace

| Criterion | PyPI | Git Clone | uv Workspace (Dogfooded) |
|---|---|---|---|
| Setup friction | `uv sync` (zero) | Manual clone + path config | `uv sync` (zero) |
| Version pinning | Exact (`==1.4.2`) | Branch/tag (approximate) | Workspace link (live) or pinned |
| Validation | Build-time only | None built-in | Continuous via vadocs hooks |
| Agent write-back | Impossible (site-packages) | Easy (local files) | Easy (workspace member) |

**Verdict:** uv Workspace with dogfooded vadocs validation for development; PyPI distribution for production deployment.

### Creative Engine: Post-Hoc Parsing vs. Structured Extraction

| Criterion | Labeled Text Parsing | Structured Extraction (Pydantic/Instructor) |
|---|---|---|
| Validation point | After generation (parser may fail on edge cases) | During generation (invalid tokens rejected) |
| Determinism | Medium — depends on parser robustness | High — schema-guaranteed output |
| Retry mechanism | Manual re-prompting | Automatic at inference layer |
| Implementation | Custom parser per output format | Schema definition + library |

**Verdict:** Structured Extraction is the industry standard for moving from experiment to production. Replaces "parsing" with "validation."

## References

- `S-26001: Gemini — Skills Architecture, Tiered Memory, and Package-Driven Infrastructure`
- [Claude Skills Inventor Transcript — Barry Zhang & Mahesh Murag (YouTube)](https://www.youtube.com/watch?v=CEvIs9y1uog)
- {term}`ADR-26013`: Just-in-Time Prompt Transformation
- {term}`ADR-26016`: Metadata-Driven Architectural Records Lifecycle
- {term}`ADR-26020`: Hub-and-Spoke Ecosystem Documentation Architecture
- {term}`ADR-26023`: MyST-Aligned Frontmatter Standard
- {term}`ADR-26027`: Model Taxonomy — Reasoning vs. Agentic Class
- {term}`ADR-26030`: Stateless JIT Context Injection
- [DSPy — Declarative Self-improving Python (Stanford)](https://github.com/stanfordnlp/dspy)
- [Instructor — Structured LLM Outputs](https://github.com/jxnl/instructor)
- [Outlines — Structured Generation](https://github.com/outlines-dev/outlines)
- [A-26001: Architecture Knowledge Base Taxonomy](/architecture/evidence/analyses/A-26001_architecture_knowledge_base_taxonomy.md)
