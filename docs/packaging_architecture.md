# Packaging & bundling architecture: medraxis vs. OpenMRS

Medraxis follows OpenMRS's **data model and concepts** (see
[`research.md`](research.md) and [`openmrs_coverage.md`](openmrs_coverage.md)),
but until now its **build/bundle architecture** had never been reviewed
against OpenMRS's. This doc records that review and the resulting decisions.

## 1. How OpenMRS actually builds and bundles its code

| Layer | Mechanism |
|---|---|
| **Backend** (`openmrs-core`) | Maven multi-module build producing a core WAR. Plugin modules are built and versioned **independently** and packaged as `.omod` files, loaded/unloaded by core's module loader **at runtime**, without recompiling core. |
| **Frontend** (`openmrs-esm-core`, O3) | Yarn workspaces + Turborepo monorepo. Each micro-frontend is built independently and loaded at runtime via Webpack Module Federation dynamic remotes, orchestrated by a single-spa shell app. |
| **Distribution** (`openmrs-distro-referenceapplication`) | A manifest file, `openmrs-distro.properties`, declares exactly which `.omod`/OWA module versions are bundled. `docker-compose.yml` assembles separate **backend**, **frontend** (nginx serving the assembled SPA), and **database** containers. Buildable via `mvn clean install` or `docker compose build`. |

The two headline traits — independently-pluggable backend modules, and
independently-deployed micro-frontends — exist because OpenMRS supports many
third-party implementers shipping their own modules/widgets against a shared
core, released on independent schedules.

## 2. Medraxis's current state (before this change)

- A single Django monolith: 13 apps under `apps/`, all registered together in
  `INSTALLED_APPS`, imported into one process. There is no runtime module
  loader and no independent versioning per app.
- Celery + Redis are configured in `config/settings/base.py` and a worker task
  exists (`apps/notifications/tasks.py`), but nothing in the repo composed a
  worker, a scheduler, or Redis/Postgres together — there was one
  `Dockerfile` and no `docker-compose.yml`. `process_due_notifications` was
  defined but never scheduled anywhere, so even a hypothetical beat process
  would have had nothing to do.
- No frontend exists yet (see `research.md` §9, "roadmap").

## 3. Decision

**3.1 Backend stays a single deployable monolith.** Medraxis does not need
OpenMRS's `.omod`/module-loader machinery: there is one team, one release
cadence, and one deployable artifact. Splitting `apps/*` into independently
installable packages would add packaging/versioning overhead (dependency
resolution between modules, a loader, compatibility matrices) to solve a
problem — independently-released third-party plugins — that medraxis doesn't
have. The existing pattern (`research.md` §8: `GlobalProperty`, typed
attributes, and "drop-in" Django apps that reuse the `Concept`/`Order`/`Obs`
spine) already gives the *extensibility* OpenMRS modules provide, without the
runtime-loading complexity.

**3.2 Adopt a `docker-compose.yml` as medraxis's distro-equivalent.** This is
the part of OpenMRS's bundling model that *does* transfer: a single declared
stack assembling everything the app needs to run together. `docker-compose.yml`
(repo root) now composes:

- `db` — `postgres:16` (matches the version pinned in `test-postgres` in
  `.github/workflows/ci.yml`).
- `redis` — `redis:7-alpine`, backing both the Django cache and the Celery
  broker/result backend.
- `web` — the existing `Dockerfile` image, unchanged (its `CMD` already runs
  `migrate && gunicorn`).
- `worker` — same image, `celery -A config worker -l info`.
- `beat` — same image, `celery -A config beat -l info`, now meaningful because
  `config/celery.py` defines a `beat_schedule` entry that dispatches
  `process_due_notifications` every 60 seconds.

No `Dockerfile` changes were needed — it already documented "Override CMD for
a worker, etc."; compose just supplies the different `command:` per service
against one built image.

**No manifest file (`openmrs-distro.properties` equivalent) was added.**
OpenMRS's manifest solves a problem medraxis doesn't have: pinning *many
independently-released module versions*. Medraxis ships one versioned
application image plus two pinned upstream images (`postgres:16`,
`redis:7-alpine`); version pins belong directly in `docker-compose.yml`
(and the image tag itself), not in a separate manifest format.

**3.3 Frontend direction (recorded now, not built).** When frontend work
starts, ship a **single SPA** rather than adopting OpenMRS's Module
Federation/single-spa machinery up front — that machinery exists to let O3
support many independently-deployed micro-frontends across a large ecosystem
of implementers, which doesn't describe medraxis's situation yet. The
forward-looking recommendation is to keep the SPA's route/feature boundaries
aligned with the existing backend verticals (`emr`, `lis`, `pharmacy`, `pos`,
`billing`, `finance`, ...) — e.g. one route subtree and state module per
vertical — so that *if* a vertical (most plausibly `lis` or `pos`, which have
the most standalone usage patterns: a lab-only or shop-only deployment) later
needs to be carved out into its own deployable micro-frontend mirroring O3's
Module Federation model, that's a refactor along an existing seam, not a
rewrite. This should not be designed or scaffolded before there's an actual
frontend to split.

## 4. Follow-ups intentionally deferred

- A full `docker compose`-based CI smoke-test job (provisioning the whole
  stack and exercising it) was not added — it would duplicate
  `test-postgres`'s service-container setup for limited marginal value over
  the existing test matrix. CI only validates `docker compose config --quiet`
  (catches syntax/interpolation errors) as part of the `docker-build` job.
- Image publishing/tagging for releases is out of scope for this change.
