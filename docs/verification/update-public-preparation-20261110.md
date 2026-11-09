# Update preparation without personal service initialization

The update preparation process only warms the public catalog. It now constructs
the real Store, IntegrationService with background synchronization disabled, and
KnowledgeAnalysisCache. Personal training services, account initialization and
HTTP listeners are left to normal application launch.

The compact projection and its invalidation contract remain unchanged. A proposed
separate cold-projection path was rejected after the unchanged-account restoration
regression exposed a profile rewrite; the rejected patch and diagnostics remain
in the local verification directory and are not part of this change.

Validation completed on disposable state:

- 32 compact startup, loading cache, update preparation and account restoration
  checks passed after rejecting that proposal.
- The new preparation check preserves an existing personal SQLite file byte for
  byte and an opaque account-session document, then verifies the warmed catalog
  through a new Store with the normal public integration and analysis inputs.
- Missing public JSON and shared Node dependencies in the initial sparse checkout
  were environment setup failures. The required exact Git input and existing
  pinned dependency were restored before the account restoration checks.

The earlier actual old-version upgrade measured 72.477 seconds and remains a
failed one-minute target. This source change does not itself establish a new
whole-upgrade timing or authorize promotion of that failed candidate.
