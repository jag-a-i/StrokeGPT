# Consolidated Learnings

## Testing Patterns
- Always use pytest for unit tests as specified in PLANNING.md
- For async methods, properly mock them using unittest.mock or create async test helpers
- Test both positive and negative cases, including edge cases like calling methods when no device is connected
- Ensure cross-platform compatibility in tests, especially for console output

## Cross-Platform Compatibility Patterns
- Avoid emoji characters in console output to ensure compatibility with Windows systems
- Test on target platforms to identify encoding issues early
- Use plain text status indicators instead of Unicode symbols for broader compatibility

## Device Detection and Control Patterns
- In Buttplug protocol v3, devices may expose actuators through multiple mechanisms:
  * Generic `device.actuators` list
  * Specific attributes like `device.linear_actuators`, `device.rotatory_actuators`
- Always check both mechanisms for maximum device compatibility
- Categorize actuators by their description strings to determine their type (vibrate, linear, rotate)

## Documentation Patterns
- Add detailed docstrings to all public methods explaining parameters, return values, and behavior
- Include comments for non-obvious code logic, especially around device detection and actuator handling
- Update README.md when adding new features or changing existing functionality
- Maintain living documents that track task completion and improvements

## Error Handling Patterns
- Gracefully handle missing methods and edge cases (e.g., calling stop() when no device is connected)
- Provide clear error messages that help with debugging
- Use proper exception handling to prevent crashes

## API and Implementation Patterns
- When implementing Protocol v3 compliance, refactor from direct method calls to actuator-based commands
- Separate server connection from device connection states with distinct status indicators
- Always validate inputs (URLs, parameters) before processing
- Maintain backward compatibility while improving functionality

## Project Management Patterns
- Preserve TASK.md as a historical record of completed work
- Follow the technology stack specified in PLANNING.md
- Use uv as the package manager for Python dependencies
- Organize code into clearly separated modules