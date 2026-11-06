# Changelog

All notable changes to PulseML are documented here.

## [1.0.0] — 2026-11-06

### Added
- Model registry with CRUD operations
- Prediction log upload with auto-computed statistics
- KS test, PSI, Chi-squared, and Wasserstein drift detectors
- Performance degradation detection (accuracy, AUC, F1, R²)
- Automatic drift analysis on each new prediction window
- Alert system with severity levels (low / medium / high)
- Dashboard API with model summaries
- React + TypeScript frontend with Tailwind CSS
- Drift timeline chart and prediction distribution comparison
- Sample data generator simulating 6 months of drift
- Docker + docker-compose deployment
- 28-test suite (15 unit + 13 integration, all passing)
