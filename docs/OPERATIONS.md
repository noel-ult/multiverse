# multiverse: verification and operations

Reviewed against [default-branch commit 91710218b4b3](https://github.com/noel-ult/multiverse/commit/91710218b4b3dcd8a915a1466816b1e07b84882f) on 2026-10-28. Start with the [developer guide](PROJECT_GUIDE.md) for installation and architecture, and the [source reference](REFERENCE.md) for exact scripts, configuration readers, routes, and source locations.

## Universe branching

Use disposable accounts and data to register/login, create a universe, branch a decision, inspect the tree/comparison, and reject unauthorized edits and invalid CSRF submissions.

These are acceptance scenarios for a maintainer to run in the documented environment. Their inclusion is not a claim that live integrations or production credentials were tested during this documentation update.

## Deployment and failure diagnosis

Apply migrations before requests. Production configuration rejects SQLite and requires a configured secret; use the documented WSGI and MySQL deployment.

## Maintaining the contract

When behavior changes, update the guide and examples in the same PR. Check the entry point and working directory before copying commands. Use the linked source readers to distinguish build-time configuration from process environment. For failures, capture the first application error, runtime version, selected mode, and redacted configuration names before later proxy or port errors.

Keep changes tied to evidence: a declared command is not proof it passes, a process health response is not a successful end-to-end workflow, and a historical report describes its own revision. Record actual check results and any unavailable external services in the PR.
