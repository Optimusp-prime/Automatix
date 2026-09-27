# ADR-0025 — Cached-method temporary lifetime patch

Status: Accepted
Date: 2026-09-27

## Context

automata-lib 9.2.0 depends on cached_method >=0.1.0. The installed
cached_method 0.1.0 descriptor stores an lru_cache callable per instance;
that cache holds only a weak method. When a cached method is called on a
temporary automaton, its returned callable can outlive the object before
invocation. The executed native DFA expression `(d - d).isempty()` raises
`RuntimeError: Bound object has been garbage collected`. The mature
documentation explicitly fixes this through an import-time runtime patch.

## Decision

During import of `automata_extensions`, install one idempotent replacement
for `cached_method.__get__`. The replacement delegates all cache lookup
and creation to the original 0.1.0 descriptor, then returns a short-lived
callable holding the instance strongly. Class-level descriptor access is
unchanged. Neither the instance nor its cache stores this new wrapper; the
underlying cache retains its weak reference and its cache_info/cache_clear
operations. Reject an unknown version or a conflicting descriptor patch
instead of changing uninspected behavior.

## Alternatives considered

- Change automata-lib or site-packages source: forbidden by project rules.
- Patch each affected upstream method: duplicates work and misses future
  cached methods.
- Bind every temporary in caller code: cannot satisfy the mature public
  chained-call contract.

## Consequences

All automata-lib cached_method descriptors in the process benefit after one
Automatix import, including native DFA. This is a deliberately global,
version-targeted runtime compatibility patch; no algorithm-result cache is
added. Tests verify idempotence, cache hits, temporary calls and garbage
collection.

## Related requirements

M9; the fixed upstream dependency is recorded in ADR-0001.

## Supersedes

None.
