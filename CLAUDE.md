# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool for querying Google Cloud Platform IAM roles and permissions. It helps users discover predefined roles and understand which permissions they include.

## Architecture

- **Entry point**: `src/gcp_iam_roles/__init__.py` - Main CLI interface using argparse
- **Database layer**: `src/gcp_iam_roles/db.py` - SQLite database management for roles/permissions/services
- **Authentication**: `src/gcp_iam_roles/auth.py` - Google Cloud authentication handling
- **Core modules**: 
  - `roles.py` - Role search and synchronization
  - `permissions.py` - Permission search and synchronization  
  - `services.py` - Service search and synchronization

The application stores data locally in `~/.local/share/gcp-iam-roles/gcp-iam-roles.db` (SQLite database).

## Development Commands

### Package Management
- `uv sync` - Install dependencies and sync lock file
- `uv run gcp-iam-roles` - Run the CLI tool directly

### Testing
- `make test` - Run all tests (help, roles, permissions, service tests)
- `make test-help` - Test CLI help functionality
- `make test-roles` - Test role search functionality
- `make test-permissions` - Test permission search functionality
- `make test-service` - Test service search functionality

### Code Quality
- `ruff format --check .` - Check code formatting
- `ruff check .` - Run linting checks

### Build and Release
- `make build` - Build wheel package in dist/
- `make clean` - Clean build artifacts and virtual environment
- `make version` - Update version with timestamp
- `make commit` - Format, lint, and commit changes
- `make release` - Full release process (build, sign, push, create GitHub release)

## Configuration

- Uses `uv` for dependency management
- Ruff configuration in `pyproject.toml` with line length 100, Python 3.13 target
- Requires Google Cloud authentication via `gcloud auth login --update-adc`
- Database auto-created on first run

## Key Features

- Search IAM roles by name pattern
- Search permissions to find which roles include them
- Search services 
- Sync roles/permissions/services from Google Cloud APIs
- Local SQLite caching for fast queries
- Bash completion support