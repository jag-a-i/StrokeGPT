####Rule: Testing & Reliability
  - Always create unit tests for new features (functions, classes, modules, etc.) using the testing framework specified in PLANNING.md.
  - After updating any logic, check whether existing unit tests need to be updated. If so, update them.
  - Tests should live in a /tests folder mirroring the main application structure.
  - Include at least:
    - 1 test for the expected use case
    - 1 test for an edge case
    - 1 test for a failure case (e.g., bad input)