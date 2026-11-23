# Release preparation — v4.3.8

Authorized November 23, 2026: publish and update existing installations.
Payload: PR #83 (#82), shared-continuity diagnostics and migration guidance.

Release pins and plugin version are 4.3.8. Existing tags and historical release
receipts remain unchanged. Publication, public-tag smoke, marketplace and installed
copy verification follow the version-and-pins merge; no publication is claimed here.

Failing first: the 4.3.8 installer expectations reported 8 failed / 7 passed against
4.3.7 source. After pin changes, all 15 installer cases pass. The four Python 3.11+
Codex installer cases pass separately under Python 3.14. Plugin validation passes
with its existing optional-icon warning. Full-pack results are in TEST.md.

Pending: GitHub CI/merge/tag/release, public bootstrap smoke, marketplace bump,
existing installation refresh, and a separately reviewed affected-client migration.
Private machine access and installation inventory stay out of this public receipt.
