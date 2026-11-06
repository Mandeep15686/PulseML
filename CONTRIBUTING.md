# Contributing to PulseML

Thank you for considering contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/your-username/pulseml.git
cd pulseml
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_db.py
uvicorn backend.main:app --reload
```

## Code Standards
- **Python**: follow PEP 8; use type hints; write docstrings for public functions
- **TypeScript**: strict mode; named exports; no `any` unless unavoidable
- **Tests**: every new feature needs tests in `tests/`; run `pytest` before PR

## Pull Request Flow
1. Fork the repo and create a feature branch (`git checkout -b feat/my-feature`)
2. Write code + tests
3. Run the full test suite: `pytest tests/ -v`
4. Push and open a PR against `main`
