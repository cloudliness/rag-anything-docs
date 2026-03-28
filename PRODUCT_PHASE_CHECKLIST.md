# Product Phase Checklist

This file tracks product work completed in this repository against the phased product build plan.

Use it as the current execution snapshot, not the long-form strategy document.

## Status Summary

- [x] Phase 1: Product Foundation And Demo Surface
- [ ] Phase 2: Ingestion Jobs, Status, And Reliability
- [ ] Phase 3: Answer Experience And Source Trust
- [ ] Phase 4: Math-Friendly And Study-Friendly Experience
- [ ] Phase 5: DIY, Technician, And Mechanic Modes
- [ ] Phase 6: Business Features And Admin Controls
- [ ] Phase 7: Performance, Scalability, And Deployment
- [ ] Phase 8: Product Refinement And Market Packaging

## Current Working Rule

- We are still following the phase plan.
- Work is allowed to pull a small dependency forward when it directly improves the current phase.
- A phase is only marked complete when its core deliverables and success criteria are satisfied, not just when some related features exist.

## Phase 1: Product Foundation And Demo Surface

Status: Complete

Completed:

- [x] Local web app scaffolded under `app/` and `web/`
- [x] Knowledge base creation and selection UI
- [x] Document upload screen wired to backend ingest
- [x] Query screen wired to backend wrapper
- [x] Multi-KB query support
- [x] Visible list of knowledge bases and documents
- [x] CLI kept as underlying plumbing while UI uses backend wrappers

Notes:

- This phase is functionally done and demoable.

## Phase 2: Ingestion Jobs, Status, And Reliability

Status: In Progress

Completed:

- [x] Asynchronous ingestion jobs
- [x] Job persistence across page refreshes
- [x] Upload progress UI
- [x] Per-document job history
- [x] Retry controls
- [x] Cancel controls
- [x] Dedicated jobs operations screen with search, filters, and sorting
- [x] Actual processed page telemetry recorded from parser output
- [x] Backend job lifecycle test coverage
- [x] Frontend UI tests for retry, cancel, and job history

Remaining:

- [ ] Split coarse job states into clearer pipeline stages such as parsing, indexing, and ready
- [ ] Surface cleaner failure categories so parser failures and downstream extraction failures are easier to distinguish
- [ ] Add background refresh or polling so job state updates arrive without user action

## Phase 3: Answer Experience And Source Trust

Status: In Progress

Completed:

- [x] Markdown answer rendering
- [x] KaTeX rendering for math output
- [x] Chunk-backed citations with document and page provenance

Remaining:

- [ ] Answer history
- [ ] Saved answers
- [ ] Export support
- [ ] Source snippet inspection panel

## Phase 4: Math-Friendly And Study-Friendly Experience

Status: Not Started

Completed Early:

- [x] KaTeX support is already in place as a prerequisite

Remaining:

- [ ] Preserve and reuse source LaTeX from parsed equations
- [ ] Add answer modes such as concise, worked explanation, beginner explanation, and study guide
- [ ] Quiz and flashcard generation
- [ ] Study note export workflows

## Phase 5: DIY, Technician, And Mechanic Modes

Status: Not Started

Remaining:

- [ ] Procedural answer formatting
- [ ] Troubleshooting-oriented output modes
- [ ] Tool, part, torque, and warning extraction
- [ ] Printable maintenance or repair summaries
- [ ] Structured checklist-style answer cards

## Phase 6: Business Features And Admin Controls

Status: Not Started

Remaining:

- [ ] Authentication and user accounts
- [ ] Organizations or workspaces
- [ ] Role-based access control
- [ ] Admin dashboards
- [ ] Audit logs and usage analytics
- [ ] Knowledge base ownership and sharing rules

## Phase 7: Performance, Scalability, And Deployment

Status: Not Started

Remaining:

- [ ] Throughput and latency tuning
- [ ] Configurable deployment profiles
- [ ] Monitoring and operational logging improvements
- [ ] Safer re-index and versioning workflows

## Phase 8: Product Refinement And Market Packaging

Status: Not Started

Remaining:

- [ ] Onboarding and empty-state improvements
- [ ] Visual polish and branding pass
- [ ] Use-case-specific templates
- [ ] Demo-ready sample workspaces and product messaging

## Latest Completed Slice

- [x] Dedicated jobs screen
- [x] Actual processed page counts from parser output
- [x] Frontend UI tests for retry, cancel, and job history rendering

## Suggested Next Slice

- [ ] Live job polling or auto-refresh
- [ ] Finer-grained ingest states
- [ ] Better ingest failure categorization in the UI