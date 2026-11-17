# Video Fil de lecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved minimalist video design without changing execution semantics.
**Architecture:** Keep Graphviz geometry and FFmpeg export. Adapt private Pillow composition and timeline, retaining the public signature and HTML player.
**Tech Stack:** Python, automata-lib 9.2.0, Graphviz, Pillow, FFmpeg.
**Spec:** ../specs/2026-11-16-video-fil-lecture-design.md

## Global Constraints

- No upstream edits; no automaton mutation or persistent algorithm caches.
- `export_animation_video(word, filename, *, fps=1.0, render_fps=30)` unchanged.
- Video 1280×720; consumed opacity 25 %; rejected suffix opacity 100 %.
- Final wording: Accepté / Refusé, never Bloqué.

## Review Focus

- Empty input: epsilon and truthful verdict without indexing a missing symbol.
- Partial DFA: first absent transition stops, suffix remains unconsumed.
- Long words: visible window keeps the failure location and suffix readable.
- Single-frame steps: timeline still terminates with the correct real state.
- Loops: smooth traversal without fading the active state to nothing.

### Task 1: Presentation, motion and verification

**Files:** Modify `automata_extensions/fa/dfa_mixins/animation_video.py`,
`automata_extensions/fa/dfa_mixins/animation.py`,
`tests/fa/test_animation_video_render.py`, `docs/IMPLEMENTATION_STATUS.md`;
create `docs/VIDEO_ANIMATION.md` and a new ADR supplementing ADR-0027.

**Interfaces:** Public export unchanged. Private `_Moment` gains a defaulted
phase for continuous interpolation; `_FrameRenderer.frame()` returns RGB 1280×720.

- [x] Add failing tests for top-left word, dimmed prefix, full-opacity red
  suffix, final-refusal last symbol, empty input, eased motion and small cadence.
- [x] Run targeted pytest and confirm failures describe the old rendering.
- [x] Implement eased phase and crossfade; lightweight word strip and unified
  verdict. Keep one layout and distance-based spline sampling.
- [x] Run targeted tests and strict typing; fix actual regressions.
- [x] Update user docs, ADR and tracker; run full pytest and inspect real MP4s.
- [x] Obtain independent review and address substantive findings; leave changes
  on isolated `feat/video-fil-lecture` branch, no merge or push.

## Execution ledger

Base: main 757dcd1. User explicitly approved execution; no additional design gate.
Native isolated worktree created. Initial restricted run reached test completion
but failed changing back to the checkout (Windows permission); rerun with access.
Ruling: use this durable ledger instead of POSIX-only task helper scripts on Windows.
Pre-flight: one cohesive renderer task, no cross-task interfaces.

Task 1 complete: baseline 1381 passed; RED 10 failed / 4 passed against old
renderer; GREEN 35 targeted passed. Full suite 1390 passed, no skips.
Strict mypy 122 files passed (including demo). One existing audioop deprecation.
Real examples: accepted267frames, final-rejected229, blocked153; all 1280×720
H.264/30fps, frames inspected. Independent reviewer found no blocking issues.
No deferred findings. Changes deliberately remain uncommitted for user review.
