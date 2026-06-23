# Adapter Integration Notes

This directory contains the legacy hardware-backed automation utilities and the adapter integration used by the web application.

## What Is Here

- low-level adapter wrappers
- command helpers for UCSI requests
- legacy automation entrypoints
- utility modules for test input and history handling

## Typical Use

Use this folder when you want to execute UCSI traffic through the external I2C adapter path rather than the platform-native Windows or Linux backends.

## Legacy Automation Flow

1. Install a compatible Python environment (virtual environment optional).
2. Connect the external adapter to the target system and the host machine.
3. Update test inputs in [User_Inputs.py](aardvark/User_Inputs.py).
4. Select the test coverage you want in [Run_TestCases.py](aardvark/Run_TestCases.py).
5. Run the test runner from a command prompt.

Example:

```bash
python aardvark/Run_TestCases.py > output.txt
```

## Notes

- The web UI can detect whether the adapter integration is available and expose adapter-backed execution paths automatically.
- Keep adapter-specific binaries, drivers, and host-specific setup outside the repository.
- Treat this directory as hardware-integration support code, not the primary web application entrypoint.

