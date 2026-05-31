# Skill: Managing Releases

This skill codifies the end-to-end process for transitioning a project version from a set of commits to a strategic, user-facing release narrative.

## 🎯 Objective
Transform technical noise (git diffs, commit logs) into a strategic narrative in `RELEASE_NOTES.md` and promotional content, while strictly avoiding context window exhaustion.

## ⚠️ Critical Constraint: Anti-Context-Bomb Pattern
**NEVER read raw `git diff` or full `CHANGELOG` outputs directly into the chat context.** Large diffs act as "token bombs" that cause the agent to forget strategic goals and drift into technical minutiae.

**The Mandatory "Disk-Buffered" Workflow:**
1. **Dump:** Redirect all raw evidence to `misc/release/<version>/raw_*.txt`.
2. **Segment:** Read raw files in small chunks or use `grep` to find signals.
3. **Synthesize:** Extract "Strategic Signals" to a separate summary file (`signals.md`).
4. **Draft:** Write the narrative based *only* on the `signals.md` file.

---

## 🛠️ Execution Pipeline

### Phase 1: Preliminary Cleanup
- **Action:** Purge processed ephemeral files from `misc/` to ensure a clean state.
- **Goal:** Remove stale plans or temporary notes from previous sessions.

### Phase 2: Disk-Buffered Evidence Gathering
- **Action 1 (Diff):** Execute `git diff v<old>..v<new> > misc/release/v<new>/raw_diff.txt`.
- **Action 2 (Changelog):** Execute `uv run tools/scripts/generate_changelog.py <old>..HEAD > misc/release/v<new>/raw_changelog.txt`.
- **Action 3 (Verification):** Use `ls -lh` to confirm file sizes. If files are > 10KB, the "Buffered Pattern" is mandatory.

### Phase 3: Segmented Strategic Synthesis
- **Action 1 (Domain Extraction):** Perform isolated passes for the following domains:
    - **Architecture:** Look for ADR changes, structural pivots, or new governance standards.
    - **Tooling/Scripts:** Look for new scripts, fixed bugs, or improved agentic workflows.
    - **Content:** Look for new articles, reorganized layers, or updated guides.
- **Action 2 (Signal Mapping):** For each domain, read the `raw_*.txt` files in segments and write "Strategic Signals" (the *Why* and the *Win*) to `misc/release/v<new>/signals.md`.
- **Action 3 (Narrative Drafting):** Load `signals.md` and draft the release notes using the **Pain $\rightarrow$ Solution $\rightarrow$ Win** framework.
    - *Avoid "neuroslop":* No "comprehensive," "robust," or "enhanced" without a concrete example.

### Phase 4: Trinity Peer Review
- **Action:** Evaluate the draft from three perspectives:
    1. **UX Critic:** Is it readable? Is the "value prop" clear?
    2. **Technical Critic:** Is it accurate? Does it miss a critical technical shift?
    3. **Strategic Critic:** Does it align with the high-level project vision?
- **Output:** Refine the narrative based on the review.

### Phase 5: Publication & Sync
- **Action 1 (Release Notes):** Update `RELEASE_NOTES.md` with the finalized narrative.
- **Action 2 (README):** Sync `README.md` if the release changed the project's core value prop or structure.
- **Action 3 (Promotion):** Draft a Telegram post in `misc/pr/tg_channel_ai_learning/` following the established Russian template.

### Phase 6: Post-Release Hygiene
- **Action:** Delete the `misc/release/v<new>/` directory.
- **Goal:** Ensure the repository does not accumulate "evidence debt."

---

## 📝 Deliverables
- [ ] `RELEASE_NOTES.md` (Updated)
- [ ] `README.md` (Synced)
- [ ] Telegram post (`.md` file)
- [ ] Git commit for the release documentation

