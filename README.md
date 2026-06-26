# IMS Rubric

This repository currently contains a minimal Streamlit application scaffold for IMS Rubric work.

## Current state

- The user interface is implemented in `/home/runner/work/IMS_Rubric/IMS_Rubric/streamlit_app.py`.
- The project is managed with `uv` and configured in `/home/runner/work/IMS_Rubric/IMS_Rubric/pyproject.toml`.
- No persistent database layer is implemented today.
- The checked-in app is a simple placeholder screen rather than a completed product workflow.

## Repository layout

```text
IMS_Rubric/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── database.md
│   └── developer.md
├── pyproject.toml
├── streamlit_app.py
└── uv.lock
```

## Local development

1. Install `uv`.
2. Sync dependencies:

   ```bash
   uv sync
   ```

3. Start the Streamlit app:

   ```bash
   uv run streamlit run streamlit_app.py
   ```

The default app starts a single Streamlit page with placeholder content.

## Documentation

- Architecture: `/home/runner/work/IMS_Rubric/IMS_Rubric/docs/architecture.md`
- Database: `/home/runner/work/IMS_Rubric/IMS_Rubric/docs/database.md`
- Developer guide: `/home/runner/work/IMS_Rubric/IMS_Rubric/docs/developer.md`
