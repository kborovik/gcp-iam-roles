.EXPORT_ALL_VARIABLES:
.ONESHELL:
.SILENT:

MAKEFLAGS += --no-builtin-rules --no-builtin-variables

PATH := $(HOME)/.cargo/bin:$(abspath .venv)/bin:$(PATH)

.PHONY: version commit release

ifneq (,$(wildcard pyproject.toml))
NAME := $(shell sed -n 's/^name = "\(.*\)"/\1/p' pyproject.toml)
MODULE := $(shell sed -n '/\[project.scripts\]/!b;n;p' pyproject.toml | cut -d':' -f1 | cut -d'"' -f2)
VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
endif

help: setup
	echo "Settings:"
	echo "  NAME:    $(NAME)"
	echo "  VERSION: $(VERSION)"
	echo "Help:"
	echo "  make test    - Test Python package"
	echo "  make clean   - Reset Python environment"
	echo "  make commit  - Create Git commit"
	echo "  make release - Build Python Wheel and publish to GitHub"

setup: $(uv_bin) .gitignore .venv uv.lock

test: test-help test-roles test-permissions test-service

test-help:
	uv run gcp-iam-roles
	uv run gcp-iam-roles --help

test-roles:
	uv run gcp-iam-roles --status
	uv run gcp-iam-roles --role cloudquotas.viewer
	uv run gcp-iam-roles --role roles/cloudprofiler.user
	uv run gcp-iam-roles --role vvvvvvv

test-permissions:
	uv run gcp-iam-roles --status
	uv run gcp-iam-roles --permission compute.addresses.createTagBinding
	uv run gcp-iam-roles --permission vvvvvvv

test-service:
	uv run gcp-iam-roles --status
	uv run gcp-iam-roles --service actions
	uv run gcp-iam-roles --service xxxxxxx

test-sync-roles:
	uv run gcp-iam-roles --sync-roles
	uv run gcp-iam-roles --status

test-sync-services:
	uv run gcp-iam-roles --sync-services
	uv run gcp-iam-roles --status

run:
	uv run $(NAME)

build: setup
	rm -rf dist/*
	uv build --wheel

clean:
	rm -rf .venv uv.lock requirements.txt build/ dist/ *.egg-info/ src/gcp_iam_roles/__pycache__/

uv_bin := $(HOME)/.cargo/bin/uv

$(uv_bin):
	$(call header,uv - Install)
	mkdir -p $(@D)
	curl -LsSf https://astral.sh/uv/install.sh | sh

.gitignore:
	cat << EOF > $(@)
	**/__pycache__/
	**/tmp/
	EOF

.venv:
	uv venv

pyproject.toml:
	uv init --package
	uv add --dev ruff

uv.lock: pyproject.toml
	uv sync && touch $(@)

requirements.txt: uv.lock
	uv pip freeze --exclude-editable --color never >| $(@)

version: setup
	$(eval pre_release := $(shell date '+%H%M' | sed 's/^0*//'))
	$(eval version := $(shell date '+%Y.%m.%d.post$(pre_release)'))
	set -e
	sed -i 's/version = "[0-9]\+\.[0-9]\+\.[0-9]\+.*"/version = "$(version)"/' pyproject.toml
	uv sync
	git add --all

commit: setup
	set -e
	ruff format --check .
	ruff check .
	git commit -m "Patch: $(NAME) v$(VERSION)"

release: setup
	$(eval version := $(shell date '+%Y.%m.%d'))
	set -e
	sed -i 's/version = "[0-9]\+\.[0-9]\+\.[0-9]\+.*"/version = "$(version)"/' pyproject.toml
	uv sync --inexact
	git add --all
	rm -rf dist/
	uv build --wheel
	gpg -b -u E4AFCA7FBB19FC029D519A524AEBB5178D5E96C1 dist/*.whl
	git commit -m "Release: $(NAME) v$(version)" || true
	git push origin main
	gh release create $(version) --title "$(version)" --generate-notes ./dist/*.*

###############################################################################
# Google CLI
###############################################################################

google_project ?= coroil-ocrdoc-dev1
google_region ?= us-central1

google: google-config

google-auth:
	gcloud auth revoke --all
	gcloud auth login --update-adc --no-launch-browser

google-config:
	set -e
	gcloud auth application-default set-quota-project $(google_project)
	gcloud config set core/project $(google_project)
	gcloud config set compute/region $(google_region)
	gcloud config list
