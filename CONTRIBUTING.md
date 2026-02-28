# Contributing to media-downloader

Thanks for your interest in contributing!

## Quick start

```bash
git clone https://github.com/ntachukwu/media-downloader.git
cd media-downloader

# Set up dev environment
uv sync --extra dev

# Run tests
make test

# Run linting
make lint
make typecheck
```

## Development workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature
   # or
   git checkout -b fix/your-fix
   ```

2. **Write a failing test first** (TDD)

3. **Implement until tests pass**

4. **Run the full check:**
   ```bash
   make lint && make typecheck && make test
   ```

5. **Push and open a PR:**
   ```bash
   git push -u origin feature/your-feature
   gh pr create
   ```

## PR requirements

- All tests must pass
- Coverage must stay above 80%
- No lint or type errors
- One feature/fix per PR

## Code style

- Follow [Google Developer Style Guide](https://developers.google.com/style)
- Use meaningful variable/function names
- Keep functions small and focused
- Write docstrings for public APIs (see existing code for style)

## Getting help

Open an issue if you have questions.
