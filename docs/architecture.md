# Architecture

## Overview

The current application is a very small Streamlit-based web app with a single entry point:

- `/home/runner/work/IMS_Rubric/IMS_Rubric/streamlit_app.py`

At the moment, the repository is closer to a starter scaffold than a layered production system.

## Runtime model

1. `streamlit run streamlit_app.py` launches the Streamlit server.
2. Streamlit executes `streamlit_app.py`.
3. The script renders a page title and a short help message.

## Components

### Presentation layer

- `streamlit_app.py` defines the full visible UI.
- The current UI contains:
  - a title rendered with `st.title(...)`
  - a text block rendered with `st.write(...)`

### Configuration and dependency management

- `/home/runner/work/IMS_Rubric/IMS_Rubric/pyproject.toml` defines the Python project metadata and Streamlit dependency.
- `/home/runner/work/IMS_Rubric/IMS_Rubric/uv.lock` pins resolved dependency versions for reproducible environments.
- `/home/runner/work/IMS_Rubric/IMS_Rubric/.devcontainer/devcontainer.json` configures a development container for contributors using Codespaces or compatible tooling.

## Architectural characteristics

- **Single-file application:** all runtime behavior is in one Python module.
- **Server-rendered UI:** Streamlit handles request routing and page rendering.
- **No persistence layer:** there is no database integration, ORM, or data access layer.
- **No internal API layer:** there are no service, repository, or controller modules yet.

## Implications for future work

If the project grows beyond the current placeholder app, likely next architectural steps would be:

- separating UI, domain logic, and data access into dedicated modules
- adding explicit configuration for environments and secrets
- introducing automated tests alongside new application behavior
