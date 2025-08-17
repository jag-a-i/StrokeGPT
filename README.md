# StrokeGPT

StrokeGPT is an application that provides AI-powered conversation with intimate hardware control capabilities. The application combines natural language processing with device control to create an interactive experience.

## Features

- AI-powered conversational interface
- Buttplug protocol v3 compliant device control
- Support for various intimate hardware devices (vibrators, strokers, etc.)
- Web-based user interface
- Real-time device control based on conversation context

## Technology Stack

- **Backend**: Python (Flask)
- **Frontend**: JavaScript (Vanilla)
- **Device Control**: Buttplug protocol v3
- **AI Services**: LLM integration
- **Audio**: Text-to-speech services
- **Package Manager**: uv
- **Testing Framework**: pytest

## Project Structure

```
StrokeGPT/
├── app.py                 # Main Flask application
├── buttplug_controller.py # Buttplug device controller (Protocol v3)
├── llm_service.py         # Language model integration
├── audio_service.py       # Audio/text-to-speech services
├── handy_controller.py    # Handy device controller
├── background_modes.py    # Background operation modes
├── index.html             # Main frontend interface
├── static/                # Static assets (CSS, JS, images)
├── templates/             # HTML templates
├── tests/                 # Unit tests
└── docs/                  # Documentation
```

## Setup

1. Install dependencies using uv:
   ```
   uv pip install -r requirements.txt
   ```

2. Install the buttplug-py library:
   ```
   pip install buttplug-py
   ```

3. Start the Intiface Central or Buttplug server application

4. Run the application:
   ```
   python app.py
   ```

## Buttplug Controller

The buttplug controller has been updated to fully comply with Protocol v3. Key features include:

- Actuator-based device control
- Support for linear, vibration, and rotation actuators
- Thread-safe operation
- Automatic device discovery
- Graceful error handling

For detailed implementation information, see [BUTTPLUG_CONTROLLER.md](BUTTPLUG_CONTROLLER.md).

## Configuration

The application can be configured through:
- `my_settings.json` - User preferences and settings
- Environment variables
- Command-line arguments

## Testing

Run tests using pytest:
```
pytest tests/
```

## Documentation

- [BUTTPLUG_CONTROLLER.md](BUTTPLUG_CONTROLLER.md) - Detailed buttplug controller implementation
- [buttplug-controller-fixes.md](buttplug-controller-fixes.md) - Buttplug controller improvements and fixes
- [buttplug-py-error-cheatsheet.md](buttplug-py-error-cheatsheet.md) - Error handling reference
- [PLANNING.md](PLANNING.md) - Project planning and technology stack
- [TASK.md](TASK.md) - Current tasks and bug fixes
- [QWEN.md](QWEN.md) - Project rules and guidelines

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Buttplug protocol and libraries
- Intiface for the server implementation
- Open-source AI models and services