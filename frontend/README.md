# SafeGround Frontend

React/TypeScript frontend for the SafeGround community safety intelligence platform.

The frontend provides the user-facing interfaces for Scout route analysis, anonymous reporting, safety resources, maps, status tracking, and privacy-oriented navigation.

> For full-stack setup and the recommended project commands, see the [root README](../README.md).

---

# Stack

| Technology   | Purpose                              |
| ------------ | ------------------------------------ |
| React        | UI framework                         |
| TypeScript   | Type-safe application development    |
| Vite         | Development server and build tooling |
| Tailwind CSS | Styling                              |
| Zustand      | Client-side state management         |
| Axios        | API communication                    |
| Leaflet      | Interactive maps                     |

---

# Architecture

```text
┌────────────────────────────────────────────┐
│                  App.tsx                   │
└──────────────────────┬─────────────────────┘
                       │
          ┌────────────┼─────────────┐
          │            │             │
          ▼            ▼             ▼
       Layout         Pages      Components
          │            │             │
          │            │       ┌─────┴─────┐
          │            │       │           │
          │            │     Report      Scout
          │            │       │           │
          │            │    Resources     Map
          │            │
          └────────────┼────────────────────┐
                       ▼                    │
                    Zustand                │
                     Stores                │
                       │                    │
                       ▼                    ▼
                 API Services ────────► FastAPI
```

The frontend is intentionally separated into:

```text
UI
 ↓
State
 ↓
API Client
 ↓
Backend
```

---

# Directory Structure

```text
frontend/
├── Dockerfile
├── index.html
├── package.json
├── package-lock.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
│
├── public/
│
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── index.css
    │
    ├── components/
    │   ├── Layout/
    │   │   ├── MainPanel.tsx
    │   │   ├── MobileNav.tsx
    │   │   ├── QuickExit.tsx
    │   │   └── Sidebar.tsx
    │   │
    │   ├── Map/
    │   │
    │   ├── Report/
    │   │   ├── ReportForm.tsx
    │   │   ├── ReportSuccess.tsx
    │   │   └── StatusPanel.tsx
    │   │
    │   ├── Resources/
    │   │   ├── ResourcesInputs.tsx
    │   │   └── ResourcesList.tsx
    │   │
    │   └── Scout/
    │       ├── ScoutInputs.tsx
    │       └── ScoutResults.tsx
    │
    ├── hooks/
    │
    ├── pages/
    │
    ├── services/
    │   └── api.ts
    │
    ├── store/
    │   ├── useReportStore.ts
    │   ├── useResourceStore.ts
    │   └── useScoutStore.ts
    │
    └── types/
        └── index.ts
```

---

# Application Areas

The frontend is organized around the core SafeGround workflows.

## Scout

Scout provides the interface for safety-aware route analysis.

Main components:

```text
components/Scout/
├── ScoutInputs.tsx
└── ScoutResults.tsx
```

The workflow is approximately:

```text
Enter journey
     ↓
Submit Scout request
     ↓
Backend performs safety analysis
     ↓
Receive route/safety results
     ↓
Display results and warnings
```

The map components provide geographic visualization where route data is available.

---

# Reporting

Anonymous incident reporting is implemented under:

```text
components/Report/
```

Components include:

```text
ReportForm.tsx
ReportSuccess.tsx
StatusPanel.tsx
```

The expected workflow is:

```text
Complete report
     ↓
Submit anonymously
     ↓
Receive receipt information
     ↓
Check report status when needed
```

The frontend should not introduce unnecessary identity or account requirements into this flow.

---

# Safety Resources

Safety-resource functionality is implemented under:

```text
components/Resources/
```

Components include:

```text
ResourcesInputs.tsx
ResourcesList.tsx
```

Users can search/browse available safety resources based on the application's supported criteria.

---

# Quick Exit

The quick-exit interface is implemented through:

```text
components/Layout/QuickExit.tsx
```

The feature is intended to provide a fast way to leave the SafeGround interface.

The implementation should avoid retaining unnecessary navigation state when the user activates the exit action.

---

# Layout

Shared application layout components are located under:

```text
components/Layout/
```

Current components:

* `MainPanel`
* `Sidebar`
* `MobileNav`
* `QuickExit`

The application is designed with mobile use in mind, particularly for users accessing safety-related functionality from phones.

---

# Maps

Map functionality lives under:

```text
components/Map/
```

The application uses **Leaflet** for geographic visualization.

Maps are used to present route and safety information without making the map itself responsible for business logic.

---

# State Management

Zustand stores are located under:

```text
src/store/
```

Current stores include:

```text
useScoutStore.ts
useReportStore.ts
useResourceStore.ts
```

Each store is responsible for state associated with a particular application workflow.

Conceptually:

```text
Scout UI
   ↓
useScoutStore
   ↓
API service
   ↓
Backend
```

The same pattern is used for reports and resources.

---

# API Integration

API communication is centralized under:

```text
src/services/api.ts
```

This keeps HTTP communication separate from individual UI components.

The frontend communicates with the FastAPI backend through HTTP APIs.

Development endpoints:

```text
Frontend:
http://localhost:5173

Backend:
http://localhost:8000
```

When the backend URL or API prefix changes, update the frontend's API configuration rather than hardcoding URLs throughout components.

---

# Types

Shared frontend TypeScript types are located under:

```text
src/types/index.ts
```

API responses and component state should use these types wherever practical.

This keeps the frontend contract explicit and reduces accidental mismatch between backend responses and UI expectations.

---

# Hooks

Reusable React hooks belong under:

```text
src/hooks/
```

Hooks should contain reusable UI/application behavior rather than duplicating logic across components.

---

# Environment Configuration

Vite environment variables are exposed to client-side code through the `VITE_` prefix.

For example:

```env
VITE_API_URL=http://localhost:8000
```

Only values intended to be available to browser code should use the `VITE_` prefix.

**Never place secrets, AWS credentials, private API keys, or other server-side credentials in frontend environment variables.**

---

# Running the Frontend

The recommended project-level commands are provided by the root Makefile.

Start the frontend container:

```bash
make start-frontend
```

View frontend logs:

```bash
make logs-frontend
```

Open a shell:

```bash
make shell-frontend
```

Build the frontend image:

```bash
make build-frontend
```

---

# Local Vite Development

For frontend development without running the frontend container:

```bash
make setup-frontend
make run-frontend-local
```

The development server is available at:

```text
http://localhost:5173
```

Vite provides hot module replacement during development.

---

# Production Build

Build the frontend:

```bash
npm run build
```

The generated production assets are produced by Vite.

When using the Docker workflow, the frontend Docker image handles the build/runtime configuration defined by the project's Docker setup.

---

# Development Workflow

A typical frontend development cycle is:

```text
1. Start backend
       ↓
2. Start frontend
       ↓
3. Modify React/TypeScript code
       ↓
4. Vite hot reloads
       ↓
5. Test API interaction
       ↓
6. Run build
```

Full-stack development:

```bash
make start
```

Frontend-focused development:

```bash
make start-backend
make run-frontend-local
```

---

# Component Guidelines

### Keep components focused

A component should have a clear UI responsibility.

For example:

```text
ScoutInputs
```

should focus on collecting Scout input rather than implementing the Scout agent's business logic.

### Use stores for workflow state

Shared workflow state should live in the relevant Zustand store rather than being duplicated across unrelated components.

### Keep API calls centralized

Prefer:

```text
Component
   ↓
Store / service
   ↓
api.ts
   ↓
Backend
```

rather than embedding Axios calls throughout the component tree.

### Keep business logic on the backend

The frontend should handle:

* User interaction
* Presentation
* Local UI state
* API communication
* Map visualization

Safety analysis, incident processing, persistence, and agent orchestration belong to the backend.

---

# Privacy Considerations

SafeGround is designed as a privacy-first application.

The frontend should therefore avoid introducing unnecessary tracking or identity collection.

In particular:

* Do not add analytics that identify users without an explicit architectural decision.
* Do not persist sensitive report content unnecessarily in browser storage.
* Do not store backend secrets in frontend environment variables.
* Avoid unnecessary local history for safety-sensitive workflows.
* Keep the quick-exit mechanism easily accessible.
* Do not introduce authentication requirements into anonymous reporting unless the backend architecture explicitly changes.

---

# Responsive Design

SafeGround is intended to work across:

* Mobile phones
* Tablets
* Desktop browsers

Safety-related workflows should remain usable on small screens.

The layout contains dedicated mobile navigation components:

```text
MobileNav.tsx
```

and shared desktop layout components:

```text
Sidebar.tsx
MainPanel.tsx
```

---

# Accessibility

UI changes should preserve:

* Keyboard navigation
* Visible focus states
* Appropriate semantic HTML
* Accessible form labels
* Sufficient text readability
* Clear loading and error states
* Mobile usability

Interactive controls should communicate their state clearly to users.

---

# Error and Loading States

Network operations should account for:

```text
Loading
Success
Empty
Error
```

For safety-critical interactions, errors should provide useful next steps rather than leaving the interface in an ambiguous state.

---

# Testing

Frontend-specific tests should be added under the frontend project as the test suite grows.

At the project level, the root Makefile currently provides the main backend testing commands:

```bash
make test
make test-cov
```

Frontend build validation can be performed with:

```bash
npm run build
```

---

# Docker Development

The frontend has its own Dockerfile:

```text
frontend/Dockerfile
```

The root Docker Compose configuration exposes the Vite development server on:

```text
http://localhost:5173
```

The root Makefile should be preferred over manually invoking Docker Compose for normal development.

---

# Frontend Commands

From the repository root:

```bash
make start-frontend
make stop-frontend
make build-frontend
make logs-frontend
make shell-frontend

make setup-frontend
make run-frontend-local

make format
make lint
```

See the root [`README.md`](../README.md) for the complete Makefile reference.

---

# Related Documentation

* [`../README.md`](../README.md) — full-stack setup, environment, Makefile, Docker, and project architecture
* [`../backend/README.md`](../backend/README.md) — FastAPI, Scout agent, tools, database, services, and backend development
