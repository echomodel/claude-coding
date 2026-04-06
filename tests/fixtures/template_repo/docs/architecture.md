# Architecture

## Overview

The widget service follows a layered architecture:

```
API Layer (api.py)
    ↓
Service Layer (service.py)
    ↓
Data Models (models.py)
    ↓
Storage (pluggable)
```

## Design Decisions

- **In-memory storage by default** — keeps the service simple for
  development and testing. Production deployments can swap in a
  database-backed storage implementation.

- **Webhook system** — decoupled from the main service. Webhooks fire
  asynchronously after mutations complete. Failed deliveries are
  retried with exponential backoff.

- **Batch operations** — supported natively rather than as loops over
  single operations. Batch create returns a batch ID for tracking.

## Configuration

All configuration lives in YAML files under `config/`. The service
reads `config/defaults.yaml` at startup and merges with any
environment-specific overrides.

## Error Handling

Service-layer errors use typed exceptions (`WidgetNotFoundError`, etc.)
that the API layer maps to HTTP status codes. The API never exposes
internal error details.
