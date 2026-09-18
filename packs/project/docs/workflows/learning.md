# Learning policy

This is the authoritative learning policy. `.agent/LEARNINGS.md` stores records;
root entries and skills link here instead of maintaining separate mode definitions.

## Modes and authorization

Read the declared mode in PLAN's Learning Mode section or the user's explicit
instruction. Missing mode means OFF; conflicting modes are UNCONFIRMED and capture
waits for clarification. Installation, updating, and checkpointing never enable it.

- OFF: add no entries, including candidates. Do not silently start a learning loop.
- CAPTURE: record only relevant, bounded candidates or gated lessons in LEARNINGS.
  Do not modify instructions, skills, plugins, or native settings as learning capture.
- APPLY: the same capture gates apply; propose specific instruction/skill/plugin
  edits. Apply only changes the user has authorized, with validation and rollback.
  This mode is not blanket permission to apply suggestions.

## Promotion gate

A candidate is unapproved and has no standing authority. Promote a lesson only when
it recurred on at least two distinct evidenced occasions OR the user explicitly
confirmed the lesson. Repeating the same observation twice is not recurrence.
Record evidence locators, the generalized lesson, and the future action it changes.
A one-off unconfirmed observation stays a candidate or is discarded.

An adopted lesson is a validated record, not an automatic edit to another policy.
Any proposed behavioral policy change remains subject to the APPLY authorization
rule. Direct user requests to edit a skill are ordinary authorized work, not an
implicit change of learning mode.

## Bound the record

Use separate Candidates and Adopted lessons sections. Before adding, deduplicate
and merge overlapping records. At an enabled learning review, triage candidates,
consolidate weak/repeated lessons, and retire obsolete ones with a short reason.
Aim for at most 24 active adopted lessons; exceeding that calls for consolidation,
not silent deletion of still-useful constraints. Keep a short retired summary or
link to preserved history rather than appending a diary or endless review log.
Do not install a cron job, loop, hook, or automatic capture service by default.

These are advisory agent rules. No background learner or automatic promotion
engine ships with this pack. Checks verify the contract and that the advisory
checkpoint helper makes no writes; live model compliance remains UNCONFIRMED.
