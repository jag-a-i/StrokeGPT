# Project Rules for Qwen Code

## Project Management
- Always use `uv` as the package manager for this project.

## Code Structure & Modularity
- Never create a file longer than 500 lines. If a file approaches this limit, your task is to refactor it into smaller, logical modules.
- Organize code into clearly separated modules, grouped by feature or responsibility.
- Use clear, consistent imports (prefer relative imports within packages).

## Testing & Reliability
- Always create unit tests for new features (functions, classes, modules, etc.) using the testing framework specified in PLANNING.md.
- After updating any logic, check whether existing unit tests need to be updated. If so, update them.
- Tests should live in a /tests folder mirroring the main application structure.
- Include at least:
  - 1 test for the expected use case
  - 1 test for an edge case
  - 1 test for a failure case (e.g., bad input)

## Core AI Behavior
- Never assume missing context. If a request is ambiguous, ask clarifying questions.
- Never hallucinate libraries, functions, or packages – only use known, verified components relevant to the project's tech stack.
- Only use technologies specified in PLANNING.md.
- Always confirm file paths and module names exist before referencing them in code or tests.
- Never delete or overwrite existing code unless explicitly instructed to or if part of a task from TASK.md.

## Documentation & Explainability
- Update README.md when new features are added, dependencies change, or setup steps are modified.
- Comment non-obvious code and ensure everything is understandable to a mid-level developer.
- When writing complex logic, add an inline `# Reason:` comment explaining the why, not just the what.
- Write documentation for every significant code construct (functions, classes, modules) using the documentation style specified in PLANNING.md.
- Create comprehensive documentation for major components (see BUTTPLUG_CONTROLLER.md as an example).

## Style & Conventions
- Use the primary language specified in PLANNING.md.
- Follow the coding style guide and use the recommended formatter specified in PLANNING.md.
- Use the recommended data validation and framework libraries specified in PLANNING.md.