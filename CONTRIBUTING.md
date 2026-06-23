# Contributing

This project accepts improvements to decoding accuracy, command coverage, platform support, UI behavior, documentation, and packaging.

## Before You Start

- Use the root-level [app.py](/c:/lalat/persional/opensource/ucsi-decoder-webapp/app.py) as the active runtime entrypoint.
- Keep changes focused. Avoid mixing decoder changes, UI refactors, and packaging updates in the same pull request unless they are tightly coupled.
- If you add or change a decoder, validate the affected command path with representative sample payloads.

## Development Setup

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start the app with `python app.py`.
4. Open `http://localhost:5000` in a browser.

## Contribution Workflow

1. Fork the repository.
2. Create a branch with a clear name such as `feature/add-get-cam-cs-decode` or `fix/linux-response-byte-order`.
3. Make the smallest practical change that solves the issue.
4. Test the exact flow you changed.
5. Update documentation when behavior, setup, or supported features change.
6. Open a pull request with a clear description of the problem, change, and validation performed.

## Pull Request Expectations

- Explain the user-visible behavior change.
- Call out any platform-specific impact on Windows, Linux, or adapter-backed execution.
- Include sample input and output when modifying decoders.
- Do not commit generated artifacts, local logs, or environment-specific binaries.

## Scope Guidance

Good contributions include:

- UCSI command or response decoder improvements
- More accurate field interpretation
- Bug fixes in command formatting or platform execution
- UI fixes that improve decode and execution workflows
- Documentation updates that reflect actual repository behavior

Changes that need extra care:

- Widening the active runtime away from [app.py](/c:/lalat/persional/opensource/ucsi-decoder-webapp/app.py)
- Adding new external runtime dependencies
- Modifying packaging behavior in [scripts/UCSIDecoder.spec](/c:/lalat/persional/opensource/ucsi-decoder-webapp/scripts/UCSIDecoder.spec)
- Updating bundled hardware adapter integration files

## Code Style

- Follow the existing Python and front-end style already used in the repository.
- Prefer small, readable functions over broad rewrites.
- Keep comments brief and only when they add real context.

## Security

If you find a security-sensitive issue, follow the reporting guidance in [SECURITY.md](/c:/lalat/persional/opensource/ucsi-decoder-webapp/SECURITY.md) instead of opening a public issue with exploit details.