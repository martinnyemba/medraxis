# Medraxis Frontend

A single-page application (SPA) for the Medraxis Unified Healthcare Platform.
It is the web client for the Django REST API under `/api/v1/`.

Built with **React + TypeScript + Vite**, **Tailwind CSS + shadcn/ui**,
**TanStack Query** (server state) and **React Router**. The architecture follows
[`docs/packaging_architecture.md`](../docs/packaging_architecture.md) §3.3: a
single SPA whose route/feature folders are aligned 1:1 with the backend
verticals (`emr`, `lis`, `pharmacy`, `pos`, `billing`, `finance`, …), so any
vertical can later be carved out along an existing seam.

## Status

| Area | State |
|---|---|
| App shell, auth (JWT + silent refresh), tenant switcher | ✅ Built |
| **EMR** — patient registry, registration, visits, encounters, observations | ✅ Built |
| **LIS** — worklist, ordering, specimen accession/collect/receive, result worksheet (enter → verify → release), test catalog, report/label PDFs | ✅ Built |
| **POS** — sales list, terminal (product search → cart → location), complete (stock issue), payments, receipt PDF, customers | ✅ Built |
| Pharmacy, Inventory, Billing, Finance | 🚧 Routed as "coming soon" (backend API already exists) |

## Prerequisites

- Node.js 20+ (developed on Node 22)
- A running Medraxis backend (see the [root README](../README.md)). By default
  the dev server proxies API calls to `http://localhost:8000`.

## Getting started

```bash
cd frontend
npm install

# Make sure the Django backend is running on :8000 in another terminal:
#   (from the repo root) python manage.py runserver

npm run dev          # http://localhost:5173
```

Sign in with any backend user account (e.g. a Django superuser created via
`python manage.py createsuperuser`).

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite dev server with API proxy |
| `npm run build` | Type-check (`tsc -b`) and build for production into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Run ESLint |

## Configuration

Vite only exposes env vars prefixed with `VITE_`. Copy `.env.example` to
`.env.local` to override:

- `VITE_API_BASE_URL` — backend origin in production (blank in dev → use proxy).
- `VITE_API_PROXY_TARGET` — dev-proxy target (default `http://localhost:8000`).

In development the Vite proxy forwards `/api`, `/fhir` and `/media` to the
backend so the app runs same-origin (no CORS). In production, build the SPA and
serve `dist/` from any static host, pointing `VITE_API_BASE_URL` at the API.

## Project structure

```
src/
  lib/
    api/            # typed fetch client (JWT refresh, X-Organization, envelopes)
      endpoints/    # auth, users, tenancy
    format.ts       # patient-name / age / date helpers
    queryClient.ts  # TanStack Query config
  components/
    ui/             # shadcn/ui primitives (button, dialog, table, select, …)
    common/         # PageHeader, Pagination, Empty/Error states
    layout/         # AppShell, Sidebar, OrgSwitcher, UserMenu
  features/
    auth/           # AuthContext, LoginPage, ProtectedRoute
    tenancy/        # TenantContext (facility switcher)
    dashboard/      # landing page
    emr/            # EMR vertical (patients, visits, encounters, observations)
    lis/            # Laboratory vertical (worklist, ordering, specimens, results)
    pos/            # Point-of-sale vertical (sales, terminal, payments, customers)
    inventory/      # shared product API (used by the POS cart)
    placeholder/    # "coming soon" pages for unbuilt verticals
  App.tsx           # routing (per-vertical code-split lazy routes)
  main.tsx          # providers (QueryClient, Toast)
```

Each vertical's routes are lazy-loaded as a separate bundle, so a module's
code only loads when its routes are visited — keeping the boundaries the
backend verticals already define.

## How auth & tenancy work

- **Login** posts to `/api/v1/auth/token/`; the access + refresh tokens are
  stored in `localStorage`. The API client adds `Authorization: Bearer …` and,
  on a `401`, transparently refreshes once via `/auth/token/refresh/` before
  retrying. A failed refresh clears the session and redirects to `/login`.
- **Tenancy**: the facility switcher lists `organizations/mine/` and sets the
  active `X-Organization` header on every request; switching invalidates cached
  tenant-scoped data so lists refetch for the new facility.
- **Privilege gating**: `users/me/` returns the user's OpenMRS-style privileges;
  the UI hides actions (e.g. "Register patient" requires `Add Patients`) the
  user lacks — the backend remains the source of truth and re-checks every call.
