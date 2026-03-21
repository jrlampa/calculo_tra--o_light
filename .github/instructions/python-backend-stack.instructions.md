---
name: "Python Backend Stack Conventions"
description: "Use when: FastAPI, Django, Python backend, services, repositories, pydantic, sqlalchemy, tortoise, pytest, test coverage"
applyTo:
  - "**/*.py"
---
# Python Backend Conventions

Apply these defaults automatically for Python backend work. Do not ask which base structure to use unless a direct conflict exists with current code.

## Coding Standard
- Follow PEP 8.
- Use typing in all functions and methods (inputs and return types).
- Keep modules small and responsibility-focused.

## Architecture
- Use layered architecture by default:
Controller -> Service -> Repository -> Model
- Keep business rules in Services.
- Keep persistence details in Repositories.
- Keep transport framework concerns in Controllers.

## Validation and ORM
- Use Pydantic for request/response validation and parsing.
- Use SQLAlchemy or Tortoise ORM for data access.
- Avoid raw SQL unless needed for performance-critical paths and document why.

## Testing Rules
- Use Pytest.
- Target 100% coverage in Service layer code.
- Maintain `conftest.py` fixtures for reusable setup.
- Use mocks/fakes for external calls (HTTP, queues, third-party APIs, cloud SDKs).
- Cover happy path, edge cases, and failure modes.

## Error Handling
- Use semantic HTTP status codes where applicable.
- Normalize error payloads and logging fields.
- Never leak secrets, tokens, or stack traces in client-facing responses.