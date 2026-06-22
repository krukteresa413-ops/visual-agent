# LS0 Green Report

- Timestamp: 2026-06-20T19:45:51
- Base Commit Before LS0 Tag: ba54e37
- Tag: baseline-v1 (to be created after this report is committed)

## Router Baseline

Command:
`cd app/backend && .venv/bin/python -m pytest tests/meta/test_router_inventory.py -q`

Result:
`1 passed in 0.01s`

Snapshot:
`app/backend/tests/meta/router_baseline.json`

Registered routers: 29

## Backend

Command:
`cd app/backend && .venv/bin/python -m pytest tests/ -x -q`

Result:
`494 passed, 45 warnings in 87.81s`

Notes:
- Test count increased from 493 to 494 because LS0 added `tests/meta/test_router_inventory.py`.
- Warnings are existing dependency/runtime warnings: Starlette/httpx deprecation, SQLAlchemy datetime.utcnow deprecation, EasyOCR/Torch deprecations, and one AsyncMock runtime warning already present in image generation tests.

## Frontend Build

Command:
`cd frontend && npm run build`

Result:
`vite build completed successfully`

Artifacts:
- CSS: `dist/assets/index-DYc1OVX6-1781955887296.css`
- JS: `dist/assets/index--DcbJ81p-1781955887296.js`

Warning:
- Vite chunk size warning remains non-blocking and pre-existing for the current bundle shape.

## SPA Cache Gate

Command:
`cd /opt/visual-agent && ./frontend/scripts/verify_spa_cache.sh http://127.0.0.1`

Result:
`PASS: index no-cache and 2 hashed bundles are immutable`

## Scope Notes

- LS0 added only router baseline metadata and this report.
- Existing dirty worktree changes are being frozen as the production baseline; no LS1 provider inventory work is included in this report.
- Lovart shell-related files, if present in the existing worktree, are treated as pre-existing production state for LS0, not new LS1 work.
