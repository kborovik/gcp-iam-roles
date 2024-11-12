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
	echo "  make run     - Run Python package command"
	echo "  make build   - Build Python package"
	echo "  make clean   - Reset Python environment"
	echo "  make version - Set Python package version"
	echo "  make commit  - Create Git commit"
	echo "  make release - Build Python Wheel + Git Tag"

setup: $(uv_bin) .gitignore tmp .venv uv.lock

test-role: setup
	uv run gcp-iam-roles --role roles/editor
	uv run gcp-iam-roles --role vertex

test-permissions: setup
	gcp-iam-roles --p compute.addresses.createTagBinding

run:
	uv run $(NAME)

build: setup
	uv build --wheel

clean:
	rm -rf .venv uv.lock requirements.txt build/ dist/ *.egg-info/

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

tmp:
	mkdir -p $(@)

.venv:
	uv venv

define INIT_PY
from .__main__ import main
__all__ = ["main", "$(MODULE)"]
endef

define MAIN_PY
def main() -> None:
    print("Hello world!")
if __name__ == "__main__":
    main()
endef

src-init:
	echo "$$INIT_PY" >| src/$(MODULE)/__init__.py
	echo "$$MAIN_PY" >| src/$(MODULE)/__main__.py
	ruff format .

pyproject.toml:
	uv init --package
	uv add --dev ruff

uv.lock: pyproject.toml
	uv sync --inexact && touch $(@)

requirements.txt: uv.lock
	uv pip freeze --exclude-editable --color never >| $(@)

version:
	$(eval pre_release := $(shell date '+%H%M' | sed 's/^0*//'))
	$(eval version := $(shell date '+%Y.%m.%d.post$(pre_release)'))
	set -e
	sed -i 's/version = "[0-9]\+\.[0-9]\+\.[0-9]\+.*"/version = "$(version)"/' pyproject.toml
	uv sync --inexact
	git add --all

commit: version
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
	gpg --detach-sign dist/*.whl
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