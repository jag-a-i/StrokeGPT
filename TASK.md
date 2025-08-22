# Task Plan: Investigate and Fix MCP Shrimp Task Manager Indexing Issue

## 1. Objective
The primary objective is to diagnose and resolve the "Code index is not ready for search" error within the MCP Shrimp Task Manager integration for this workspace. This plan will be executed using the Shrimp Task Manager itself to dog-food the tooling and ensure a robust, repeatable fix.

## 2. Scope
- **In Scope:**
    - Reproducing the indexing failure.
    - Analyzing the `mcp-shrimp-task-manager` codebase to find the root cause.
    - Implementing a fix that includes a safe fallback mechanism (e.g., ripgrep) if indexing fails.
    - Adding health checks and a self-healing/rebuild mechanism for the index.
    - Creating unit and integration tests for the fix.
    - Documenting the solution and updating memory logs.
- **Out of Scope:**
    - A full rewrite of the indexing service.
    - Addressing performance issues unrelated to the indexing failure.

## 3. Phases and Tasks

### Phase A: Setup and Reproducibility
*   **Task A1: Acquire and Inspect Shrimp Task Manager Repo**
    *   **Description:** Clone or locate the `mcp-shrimp-task-manager` repository within the workspace to analyze its code.
    *   **Acceptance Criteria:** The full codebase is accessible locally.
*   **Task A2: Validate Local Environment**
    *   **Description:** Ensure the local environment can build and run the Shrimp tooling (Node.js, npm/uv, etc.).
    *   **Acceptance Criteria:** `npm install` and `npm run build` (or equivalent) succeed without errors. Project tests pass.
*   **Task A3: Reproduce Indexing Failure**
    *   **Description:** Create a controlled test case that reliably reproduces the "Code index is not ready for search" error. Capture all relevant logs.
    *   **Acceptance Criteria:** The error is reproduced, and logs are saved for analysis.

### Phase B: Root-Cause Analysis
*   **Task B1: Analyze Indexing Service**
    *
