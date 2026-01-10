# Scripts

This folder contains helper scripts for development and operations.

- Dev orchestration scripts
- Data seeding or sample generation
- Utility tools for CI and linting

Available scripts:
- `dev.ps1` — starts backend and frontend as background jobs (stops when terminal closes)
- `start-detached.ps1` — starts backend and frontend in separate persistent windows (continues running even if VS Code closes or screen locks)
- `stop.ps1` — stops backend and frontend by port (8000, 5173)
- `smoke.ps1` — quick backend health/datasets checks

For persistent runs (survives VS Code/screen lock):
```powershell
.\scripts\start-detached.ps1
```

To stop:
```powershell
.\scripts\stop.ps1
```
