# Contributing to Memlyze

Thank you for your interest in contributing to Memlyze!

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/Memlyze.git
cd Memlyze

# Install in development mode
cd tracer
pip install -e .

# Run examples
cd ../examples
python 01_leak_simulation.py
```

## Project Structure

```
Memlyze/
├── tracer/          # Python memory tracer (Phase 1) ✅
├── analyzer/        # Rust analysis engine (Phase 2) 🚧
├── web-ui/          # React visualization (Phase 3) 🚧
├── cli/             # Rust CLI tool (Phase 4) 🚧
├── docs/            # Documentation
├── examples/        # Example programs
└── benchmarks/      # Performance tests
```

## How to Contribute

### Reporting Bugs

File an issue with:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Trace file (if applicable)

### Feature Requests

We're currently working through phases:
- **Phase 1**: Python tracer (✅ Complete)
- **Phase 2**: Rust analyzer
- **Phase 3**: Web visualization
- **Phase 4**: Advanced features

Check the roadmap before requesting features!

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Ensure tests pass
6. Commit with clear messages
7. Push to your fork
8. Open a pull request

### Code Style

**Python**:
- Follow PEP 8
- Use type hints where possible
- Document functions with docstrings
- Run `black` and `isort` before committing

**Rust** (Phase 2+):
- Follow Rust conventions
- Run `cargo fmt` and `cargo clippy`
- Document public APIs

### Testing

```bash
# Python tests (Phase 1)
cd tracer
python -m pytest tests/

# Benchmarks
cd ../benchmarks
python benchmark_overhead.py
```

### Documentation

- Update relevant docs in `docs/`
- Update README if adding features
- Add examples for new functionality

## Areas Needing Help

### Phase 1 (Current)
- [ ] More comprehensive tests
- [ ] C extension for lower overhead
- [ ] Windows compatibility testing
- [ ] macOS compatibility testing

### Phase 2 (Next)
- [ ] Rust analyzer implementation
- [ ] Leak detection algorithms
- [ ] Reference chain tracking
- [ ] Performance optimizations

### Phase 3 (Future)
- [ ] React UI design
- [ ] Canvas rendering optimizations
- [ ] WASM integration
- [ ] UI/UX improvements

## Code of Conduct

Be respectful, inclusive, and constructive. We're building this together!

## Questions?

Open a discussion or reach out to maintainers.

Thank you for contributing! 🎉

