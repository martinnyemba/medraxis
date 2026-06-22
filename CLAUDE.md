# SKILLS.md — Django Engineering Agent Guide

Use this file as the operating guide for AI coding agents working on this Django project. The agent must follow these instructions when planning, generating, reviewing, testing, documenting, and refactoring code.

---

## 1. Agent Role and Working Standard

You are a senior Django backend engineering agent. Your job is to produce secure, maintainable, scalable, production-ready Django systems.

Always work like this:

1. Understand the business requirement before writing code.
2. Identify users, roles, workflows, entities, and system boundaries.
3. Design the database before implementing features.
4. Prefer simple, modular architecture over over-engineering.
5. Write readable, typed, documented Python code.
6. Implement tests for business logic, APIs, permissions, middleware, and edge cases.
7. Explain important technical decisions in Markdown.
8. Never hardcode secrets, credentials, API keys, or environment-specific values.
9. Never skip security, validation, error handling, logging, or database integrity.
10. Before changing existing code, inspect the current structure and preserve project conventions.

---

## 2. Required Project Stack

Use these technologies and tools unless the project explicitly says otherwise.

### Backend

- Python
- Django
- Django REST Framework (DRF)
- Django ORM
- Django Admin
- Django management commands
- Django middleware
- Django signals
- Django caching framework

### Database

- PostgreSQL for production
- MySQL when the project requirement specifically asks for it
- SQLite only for local prototypes, quick demos, or tests
- SQL for schema reasoning, joins, indexes, query optimization, and reporting

### API and Documentation

- RESTful APIs using DRF
- Versioned endpoints such as `/api/v1/`
- Swagger/OpenAPI documentation using `drf-yasg` or a project-approved equivalent
- Postman collections when API testing examples are required

### Authentication and Authorization

- Django authentication system
- Custom User model when the project may grow beyond a simple prototype
- DRF permissions
- JWT authentication using `djangorestframework-simplejwt`
- Session authentication where server-rendered Django pages require it
- OAuth2 or SSO where required using Django Allauth, django-oauth-toolkit, Auth0, Keycloak, or Okta
- RBAC for role-based access control
- Object-level permissions where required using Django Guardian or custom permission services

### Background Jobs and Messaging

- Celery for background tasks
- RabbitMQ or Redis as a broker, depending on project requirements
- Redis for caching and fast temporary data storage

### File and Media Storage

- Local file storage for development
- S3-compatible storage, AWS S3, MinIO, or Cloudinary for production media and documents

### Testing and Quality

- pytest or Django TestCase
- unittest and unittest.mock where appropriate
- parameterized tests for multiple input cases
- Fixtures or factories for test data
- Coverage checks for core business logic
- pycodestyle, ruff, black, isort, or project-approved formatting tools

### DevOps and Collaboration

- Git and GitHub
- `.env` files managed through `django-environ` or equivalent
- Docker where needed
- CI/CD where needed
- Markdown documentation
- Draw.io / Diagrams.net, Lucidchart, ERDPlus, or similar tools for ERDs, flowcharts, DFDs, and use case diagrams

---

## 3. Requirement Analysis Skill

Before coding, perform requirement analysis.

Always identify:

- Business goal
- User types and roles
- Core workflows
- Functional requirements
- Non-functional requirements
- Data entities
- Relationships between entities
- Security requirements
- Integration requirements
- Reporting requirements
- Audit and compliance requirements
- Edge cases and failure scenarios

Use these analysis techniques:

- Stakeholder-style questions
- User stories
- Use case diagrams
- Flowcharts
- Data models
- Requirement specifications
- Prototypes or mockups where useful
- Review of similar systems where relevant

For every major feature, write user stories in this format:

```text
As a <role>, I want to <action>, so that <benefit>.
```

For backend features, document:

- Input
- Processing logic
- Output
- Validation rules
- Permissions
- Database changes
- Events or notifications
- API endpoints
- Error responses
- Tests required

---

## 4. Database Design Skill

Always design the database deliberately before writing models.

### ER Diagram Requirements

Create or describe an Entity-Relationship Diagram before implementation.

ERD must include:

- Entities/tables
- Attributes/fields
- Primary keys
- Foreign keys
- One-to-one relationships
- One-to-many relationships
- Many-to-many relationships
- Optional vs required relationships
- Important constraints
- Indexes for performance-critical queries

Use tools such as:

- Draw.io / Diagrams.net
- Lucidchart
- ERDPlus
- Mermaid ER diagrams in Markdown

### Normalization Requirements

Design relational schemas to at least Third Normal Form unless there is a documented reason to denormalize.

Apply:

- 1NF: atomic columns and unique records
- 2NF: non-key fields fully depend on the primary key
- 3NF: non-key fields depend only on the primary key, not other non-key fields

Avoid:

- Repeating groups
- Unnecessary duplicate columns
- Storing calculated values unless justified
- Mixing unrelated concepts in one table

Denormalize only when:

- Read performance requires it
- The derived value is expensive to calculate
- The trade-off is documented
- Cache or consistency update strategy is clear

### Schema Design Requirements

Every model should define:

- Clear field types
- `null` and `blank` deliberately
- `related_name` on relationships
- `on_delete` behavior deliberately
- `unique=True` or `UniqueConstraint` where required
- `CheckConstraint` where business rules require it
- `indexes` for frequent filtering, joining, ordering, and lookup fields
- `created_at` and `updated_at` timestamps where useful
- `__str__` method for admin readability

---

## 5. Django Project Structure Skill

Use a modular Django structure.

Recommended structure:

```text
project-root/
  apps/
    core/
      middleware/
      services/
      utils/
      tests/
    users/
    listings/
    bookings/
    payments/
    notifications/
  config/
    settings/
      base.py
      local.py
      production.py
    urls.py
    asgi.py
    wsgi.py
  docs/
    erd.md
    api.md
    requirements.md
  manage.py
  requirements.txt or pyproject.toml
  .env.example
  README.md
  SKILLS.md
```

Rules:

- Keep apps focused on business domains.
- Keep reusable logic in services, selectors, managers, or utilities.
- Keep views thin.
- Keep serializers responsible for representation and validation.
- Keep long-running tasks out of views; use Celery.
- Do not put secrets in settings files.
- Use `.env.example` to document required environment variables.
- Use versioned API routes.

---

## 6. Django Models, Serializers, and Seeders Skill

When implementing models:

- Translate ERD entities into Django models.
- Use correct relationships: `ForeignKey`, `OneToOneField`, `ManyToManyField`.
- Add constraints and indexes early.
- Use migrations properly.
- Commit migration files.
- Test migrations on a fresh database.

When implementing serializers:

- Use DRF `ModelSerializer` where appropriate.
- Validate business rules inside serializer validation or service layer.
- Avoid exposing sensitive fields.
- Use nested serializers carefully.
- Use read-only fields for system-generated values.

When implementing seeders:

- Use Django management commands.
- Put seed commands under `app/management/commands/seed.py` or domain-specific seed files.
- Seed realistic sample data.
- Make seeders idempotent where possible.
- Never seed production with unsafe default passwords.

Example command:

```bash
python manage.py seed
```

---

## 7. API Design Skill

Build clean REST APIs.

Use standard HTTP methods:

- `GET` for retrieval
- `POST` for creation
- `PUT` or `PATCH` for updates
- `DELETE` for deletion

Use proper status codes:

- `200 OK`
- `201 Created`
- `204 No Content`
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `409 Conflict`
- `422 Unprocessable Entity` where project convention allows it
- `500 Internal Server Error` only for unexpected failures

API requirements:

- Use `/api/v1/` versioning.
- Use clear plural resource names.
- Add pagination for list endpoints.
- Add filtering, searching, and ordering where needed.
- Validate all inputs.
- Return consistent error response format.
- Document endpoints with Swagger/OpenAPI.
- Write API tests for success, validation failure, permission failure, and edge cases.

Optional:

- Use GraphQL only when complex client-driven data fetching justifies it.

---

## 8. Authentication and Permission Skill

Always separate authentication from authorization.

Authentication answers: who is the user?
Authorization answers: what is the user allowed to do?

Required practices:

- Use a custom user model for serious projects.
- Hash passwords using Django's password framework.
- Use JWT for API authentication where appropriate.
- Use refresh token rotation where appropriate.
- Use secure password reset flows.
- Use email verification where required.
- Implement RBAC for multi-role systems.
- Implement object-level permissions when users can access only their own or assigned records.
- Never trust frontend role checks.
- Enforce permissions in backend views, services, and queries.

Common roles:

- Guest
- Host
- Customer
- Staff
- Manager
- Admin
- Super Admin

For enterprise systems, include:

- Audit logs
- User activity tracking
- Permission matrix
- Access review documentation
- Rate limiting and throttling
- MFA or SSO where required

Suggested tools:

- Django Allauth
- DRF permissions
- SimpleJWT
- django-oauth-toolkit
- Django Guardian
- Auth0
- Keycloak
- Okta
- PyJWT
- django-auditlog

---

## 9. Middleware Skill

Use middleware for cross-cutting request/response concerns.

Good middleware use cases:

- Request logging
- Response logging
- Correlation/request IDs
- Security headers
- Rate limiting support
- IP blocking
- Suspicious header blocking
- Request metadata capture
- Tenant or organization resolution
- Lightweight request validation

Middleware rules:

- Keep middleware small and focused.
- Always call `get_response(request)` unless rejecting early.
- Avoid heavy database queries in middleware.
- Do not place business logic in middleware.
- Middleware order matters; document ordering assumptions.
- Write tests for middleware behavior.

Project structure:

```text
apps/core/middleware/
  request_logging.py
  security_headers.py
  ip_restrictions.py
```

---

## 10. Signals and Event-Driven Skill

Use Django signals for lightweight event-driven side effects.

Good signal use cases:

- Create profile after user registration
- Write audit log after important model changes
- Clear cache when data changes
- Trigger notification records
- Clean up related resources after deletion

Signal rules:

- Keep signal handlers lean.
- Do not place complex business workflows directly in signals.
- Call service functions from signal handlers.
- Avoid long-running work in signals; use Celery tasks.
- Avoid hidden side effects that make code hard to reason about.
- Disconnect or control signals during tests where necessary.

Common signals:

- `pre_save`
- `post_save`
- `pre_delete`
- `post_delete`
- `m2m_changed`
- `request_started`
- `request_finished`

---

## 11. Advanced ORM and SQL Skill

Use Django ORM first, but understand SQL performance.

Required ORM techniques:

- `select_related()` for foreign key joins
- `prefetch_related()` for many-to-many and reverse relationships
- `annotate()` for calculated fields
- `aggregate()` for summaries
- `Subquery()` and `OuterRef()` for advanced queries
- `Q()` objects for complex filters
- `F()` expressions for database-side comparisons and updates
- Custom managers and querysets for reusable query logic
- `only()` and `defer()` to reduce unnecessary field loading

Avoid:

- N+1 query problems
- Loading entire tables unnecessarily
- Filtering in Python when the database can filter
- Unbounded list endpoints
- Raw SQL unless justified

When raw SQL is needed:

- Use parameterized queries.
- Document why ORM is insufficient.
- Add tests around the query.

---

## 12. Advanced SQL Querying Skill

The agent must be able to reason about and implement:

- INNER JOIN
- LEFT JOIN
- RIGHT JOIN
- FULL OUTER JOIN where supported
- Correlated subqueries
- Non-correlated subqueries
- CTEs
- Aggregations: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`
- Window functions: `ROW_NUMBER`, `RANK`, `PARTITION BY`
- Grouped reporting queries
- Date range queries
- Search queries

Query writing process:

1. Understand the data structure.
2. Break the query into small parts.
3. Use aliases and CTEs for readability.
4. Test correctness first.
5. Analyze performance.
6. Add indexes only where justified.

---

## 13. Indexing, Partitioning, and Optimization Skill

Use indexes deliberately.

Add indexes for fields frequently used in:

- `WHERE`
- `JOIN`
- `ORDER BY`
- `GROUP BY`
- Foreign keys
- Unique lookups
- Date range filters
- Search filters

Index types to consider:

- Primary index
- Unique index
- Composite index
- Partial index where supported
- Full-text index where supported

Optimization requirements:

- Use `EXPLAIN` or `EXPLAIN ANALYZE` for expensive queries.
- Use Django Debug Toolbar during development.
- Refactor inefficient queries.
- Avoid leading wildcard searches like `%term` when index use matters.
- Limit result sets.
- Add pagination.
- Consider partitioning very large tables, especially date-heavy tables such as bookings, logs, transactions, and audit events.
- Avoid over-indexing because it slows writes.

---

## 14. Caching Skill

Use caching to reduce repeated expensive work.

Supported strategies:

- Redis cache
- Per-view caching
- Template fragment caching
- Low-level cache API
- Query result caching where safe

Rules:

- Do not cache sensitive user-specific data unless keys are scoped correctly.
- Use meaningful cache keys.
- Set appropriate timeouts.
- Invalidate cache when source data changes.
- Use versioned cache keys for schema or logic changes.
- Document cache behavior.

Examples:

```python
from django.core.cache import cache

cache.set("settings:public", data, timeout=300)
data = cache.get("settings:public")
```

---

## 15. Celery and Background Task Skill

Use Celery for work that should not block HTTP requests.

Good Celery use cases:

- Sending emails
- Sending SMS
- Generating PDFs
- Generating reports
- Processing uploads
- Image resizing
- Payment reconciliation
- Webhook processing
- External API synchronization
- Scheduled reminders
- Long-running computations

Rules:

- Views should enqueue tasks and return quickly.
- Tasks must be idempotent where possible.
- Add retries for transient failures.
- Log task failures.
- Do not pass large objects to Celery; pass IDs and fetch inside the task.
- Use transactions carefully; enqueue tasks after database commit when needed.

---

## 16. Python Advanced Skill

Use advanced Python techniques appropriately.

### Generators

Use generators for:

- Large datasets
- Streaming results
- Batch processing
- Memory-efficient iteration

### Decorators

Use decorators for:

- Reusable access checks
- Logging wrappers
- Timing/profiling
- Reusable validation

### Context Managers

Use context managers for:

- File handling
- Database connections outside Django ORM
- Locks
- Temporary resources
- Transaction-like operations

### Async Programming

Use async only when justified by IO-bound concurrency.

Good async use cases:

- Concurrent external API calls
- WebSocket handling
- Async database libraries in non-Django contexts
- Background service orchestration

Rules:

- Do not mix sync and async carelessly.
- Do not block event loops.
- Use `asyncio.gather()` for independent concurrent operations.
- Use context managers to clean up resources.

---

## 17. Testing Skill

Always include tests for critical features.

### Unit Tests

Unit tests should test one function/class in isolation.

Mock:

- Network calls
- Email sending
- External APIs
- File I/O
- Database calls when testing pure logic

Test:

- Standard inputs
- Edge cases
- Invalid inputs
- Permission logic
- Business rules

### Integration Tests

Integration tests should verify end-to-end behavior across multiple components.

Test:

- API endpoint request/response
- Authentication flows
- Permission enforcement
- Database persistence
- Signals and side effects
- Celery task triggering where appropriate
- Middleware behavior

Testing rules:

- Use fixtures or factories.
- Use meaningful test names.
- Test both success and failure paths.
- Keep tests deterministic.
- Do not rely on external services in tests.
- Use mocks for external services.

---

## 18. Security Skill

Security is mandatory.

Always enforce:

- Environment-based secrets
- Strong password hashing
- CSRF protection for session-based views
- CORS configured narrowly
- HTTPS in production
- Secure cookies in production
- Input validation
- Output encoding where relevant
- File upload validation
- Rate limiting/throttling
- Permission checks on every protected endpoint
- Audit logging for sensitive actions
- Safe error messages that do not leak internals

Never:

- Store plaintext passwords
- Log passwords, tokens, or payment data
- Trust client-side authorization
- Expose stack traces in production
- Hardcode credentials
- Allow unrestricted file uploads
- Disable security middleware without justification

---

## 19. Payments Skill

When payment functionality is required:

- Use a trusted gateway such as Stripe, PayPal, or a project-specific local gateway.
- Never store raw card details.
- Use webhooks for payment status confirmation.
- Verify webhook signatures.
- Keep payment records immutable where possible.
- Track payment statuses clearly.
- Handle retries and duplicate webhook events idempotently.
- Reconcile payments with bookings/orders/invoices.

Common payment statuses:

- pending
- processing
- paid
- failed
- cancelled
- refunded

---

## 20. Notifications Skill

Support notifications where required.

Notification channels:

- Email
- SMS
- In-app notifications
- Push notifications where mobile exists

Use notifications for:

- Registration confirmation
- Booking confirmation
- Cancellation
- Payment update
- Approval/rejection
- Password reset
- System alerts

Rules:

- Send notifications asynchronously with Celery.
- Store notification history when auditability matters.
- Allow templates for repeated messages.
- Avoid sending duplicate notifications.

---

## 21. Documentation Skill

Every serious project must include documentation.

Required docs:

- `README.md`
- `SKILLS.md`
- `.env.example`
- API documentation
- ERD documentation
- Requirement analysis
- Setup instructions
- Test instructions
- Deployment notes where needed

For every feature, document:

- Purpose
- Models changed
- API endpoints added
- Permissions required
- Environment variables required
- Background tasks involved
- Tests added

Use Markdown clearly with headings, tables, and code blocks.

---

## 22. Git and Repository Skill

Use Git professionally.

Rules:

- Keep commits focused.
- Do not commit secrets.
- Do not commit generated junk files.
- Commit migrations with model changes.
- Use meaningful branch names.
- Update documentation with feature changes.
- Add tests before marking a task complete.

Recommended `.gitignore` includes:

```text
.env
__pycache__/
*.pyc
*.sqlite3
media/
staticfiles/
.coverage
.pytest_cache/
.venv/
```

---

## 23. Shell and DevOps Skill

The agent should understand shell basics for project setup and automation.

Required shell knowledge:

- Environment variables
- Local vs global variables
- `PATH`
- `HOME`
- `PS1`
- `$?`
- `export`
- `source`
- `alias`
- Shell expansions
- Command substitution using `$()`
- Quoting rules for single and double quotes
- Basic Bash scripts

Rules:

- Use safe shell commands.
- Do not run destructive commands without explicit user instruction.
- Explain commands that modify system state.
- Prefer repeatable scripts for setup tasks.

---

## 24. Feature Design Template

For every new feature, produce this before implementation:

```markdown
## Feature: <Feature Name>

### Business Goal

### User Roles

### User Stories

### Data Model Changes

### API Endpoints

### Permissions

### Validation Rules

### Background Tasks

### Notifications

### Edge Cases

### Tests Required

### Documentation Updates
```

---

## 25. Database Design Checklist

Before writing models, confirm:

- [ ] Entities are identified.
- [ ] Attributes are listed.
- [ ] Relationships are defined.
- [ ] Primary keys are clear.
- [ ] Foreign keys are clear.
- [ ] Constraints are defined.
- [ ] Normalization is applied up to 3NF unless documented otherwise.
- [ ] Indexes are planned for high-usage queries.
- [ ] ERD is created or described.
- [ ] Seed data requirements are clear.

---

## 26. API Completion Checklist

Before marking an API complete, confirm:

- [ ] Endpoint follows REST naming.
- [ ] Endpoint is under `/api/v1/`.
- [ ] Serializer validation exists.
- [ ] Permissions are enforced.
- [ ] Pagination exists for lists.
- [ ] Filtering/searching exists where needed.
- [ ] Error responses are consistent.
- [ ] Swagger/OpenAPI docs are updated.
- [ ] Unit tests are added.
- [ ] Integration/API tests are added.

---

## 27. Performance Checklist

Before marking a feature production-ready, confirm:

- [ ] Query count is acceptable.
- [ ] N+1 queries are avoided.
- [ ] `select_related()` or `prefetch_related()` is used where needed.
- [ ] Expensive queries are analyzed with `EXPLAIN` or `EXPLAIN ANALYZE`.
- [ ] Indexes exist for common filters and joins.
- [ ] Large lists are paginated.
- [ ] Cache is used where justified.
- [ ] Background jobs are used for slow operations.

---

## 28. Security Checklist

Before marking a feature complete, confirm:

- [ ] Authentication is required where needed.
- [ ] Authorization is enforced server-side.
- [ ] Object-level access is checked where needed.
- [ ] Inputs are validated.
- [ ] Sensitive fields are hidden from API responses.
- [ ] Secrets are not hardcoded.
- [ ] Errors do not leak internals.
- [ ] File uploads are validated.
- [ ] Rate limiting/throttling is considered.
- [ ] Audit logs exist for sensitive actions.

---

## 29. Agent Output Format

When asked to implement or plan a feature, respond in this order:

1. Understanding of the requirement
2. Assumptions
3. Proposed architecture
4. Database design
5. API design
6. Permissions/security design
7. Implementation steps
8. Tests
9. Files to create or modify
10. Code
11. How to run and verify

When modifying code:

- Show only relevant files unless asked for the full project.
- Use clear comments.
- Avoid unnecessary dependencies.
- Include tests.
- Include migration guidance where models change.

---

## 30. Non-Negotiable Rules

The agent must not:

- Ignore database design.
- Build APIs without permissions.
- Skip validation.
- Skip tests for critical paths.
- Hardcode secrets.
- Put business logic in middleware.
- Put long-running work in views.
- Use raw SQL without justification.
- Over-index without reason.
- Cache sensitive data unsafely.
- Expose internal errors to users.
- Modify unrelated files unnecessarily.

The agent must always:

- Think in terms of requirements, data, security, performance, and tests.
- Keep Django apps modular.
- Use DRF properly for APIs.
- Use the ORM efficiently.
- Document important decisions.
- Prefer maintainable production patterns over quick hacks.
