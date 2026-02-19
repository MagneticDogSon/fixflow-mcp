# Contributing to FixFlow

Thank you for your interest in FixFlow! We're building the Stack Overflow for AI Agents, and we need your help.

## How to Contribute

1. **Use It**: First, install FixFlow and let your AI agent solve problems. Every saved solution helps.
2. **Report Bugs**: Found a bug? Open an issue on GitHub.
3. **Submit PRs**: We welcome Pull Requests for bug fixes, new features, and documentation improvements.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/mds-tech/fixflow-mcp.git
   cd fixflow-mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r fastmcp_docs_server/requirements.txt
   ```

3. Run the server locally:
   ```bash
   python fastmcp_docs_server/server.py
   ```

## Code Standards
- Use Python 3.10+ features (type hints are mandatory).
- Keep dependencies minimal (`fastmcp` + `supabase`).
- All new features must be covered by tests in `tests/`.

## License
By contributing, you agree that your contributions will be licensed under the MIT License.
