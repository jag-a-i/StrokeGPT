# Task: Fix Connection Button UI Bug

## Description
The connection button in the UI shows an incorrect state on page load because the client-side JavaScript in `static/js/setup_flow.js` only checks `localStorage` and does not verify the connection status with the server at startup.

## Plan
1.  **Analyze `app.py`:** Identify the `/setup/status` endpoint and understand its response format.
2.  **Analyze `static/js/setup_flow.js`:** Examine the `SetupFlow.init()` method to understand the current initialization logic.
3.  **Modify `SetupFlow.init()`:**
    *   Add a `fetch` call to the `/setup/status` endpoint.
    *   Based on the server's response, update the UI to correctly display the connection status.
    *   Ensure the UI reflects the true connection state, overriding any stale data in `localStorage`.
4.  **Create Unit Tests:**
    *   Write a test to simulate the initial page load.
    *   Verify that a request is made to `/setup/status`.
    *   Confirm that the UI updates correctly based on the mocked server response.
