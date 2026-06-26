# Developer Documentation

## Prerequisites

- Python 3.14
- `uv`

## Project files

- `/home/runner/work/IMS_Rubric/IMS_Rubric/streamlit_app.py`: current Streamlit entry point
- `/home/runner/work/IMS_Rubric/IMS_Rubric/pyproject.toml`: project metadata and dependencies
- `/home/runner/work/IMS_Rubric/IMS_Rubric/uv.lock`: locked dependency set
- `/home/runner/work/IMS_Rubric/IMS_Rubric/.devcontainer/devcontainer.json`: optional containerized development setup

## Setup

Install dependencies:

```bash
uv sync
```

## Run locally

Start the development server:

```bash
uv run streamlit run streamlit_app.py
```

Streamlit serves the app locally on its default port unless overridden.

## Development notes

- The current app is a minimal placeholder implementation.
- There are no repository-defined test, lint, or build commands beyond dependency sync and launching the Streamlit app.
- No database setup is required because the repository does not yet include a persistence layer.

## Dev container

The repository includes a dev container configuration that:

- uses a Python 3.14 base image
- installs `uv` when needed
- syncs dependencies
- starts the Streamlit server after attach
