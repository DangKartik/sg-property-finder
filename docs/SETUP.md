# Setup guide

Detailed setup for SG Property Finder on macOS, Linux and Windows. The short version is in the [README](../README.md#run-it).

Run every command from the repository root, the folder that contains the `Makefile`:

```bash
git clone https://github.com/DangKartik/sg-property-finder.git
cd sg-property-finder
ls Makefile
```

## 1. Check the tools


The app needs:

- Python 3.11 or newer
- Node.js 24 LTS, or 22.22 or newer (npm is included)
- GNU Make

Check the installed versions:

```powershell
python --version
node --version
npm --version
make --version
```

If Python or Node.js is missing on Windows, install them with `winget`:

```powershell
winget install --id Python.Python.3.13 -e --accept-source-agreements --accept-package-agreements
winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
```

Close and reopen the terminal after installing, then run the version checks
again.

## 2. Install GNU Make

### Windows (recommended)

`winget` is included with the Windows App Installer. Install GNU Make with:

```powershell
winget install --id ezwinports.make -e --accept-source-agreements --accept-package-agreements
```

Close and reopen the terminal, then verify:

```powershell
make --version
```

If `ezwinports.make` is unavailable, use the GnuWin32 build instead:

```powershell
winget install --id GnuWin32.Make -e --accept-source-agreements --accept-package-agreements
```

If `winget` is not recognised, install **App Installer** from the Microsoft
Store first.

### macOS

Install the Xcode Command Line Tools, which include `make`:

```bash
xcode-select --install
```

Verify:

```bash
make --version
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y make
make --version
```

### Fedora

```bash
sudo dnf install -y make
make --version
```

If `make` is still not recognised after installation, close and reopen the
terminal so the updated `PATH` is loaded.

## 3. Create the environment file

Copy the example environment file and fill in the OneMap credentials.

### Windows

```powershell
Copy-Item .env.example .env
notepad .env
```

### macOS / Linux

```bash
cp .env.example .env
nano .env
```

At minimum, set:

```dotenv
ONEMAP_EMAIL=your-onemap-email
ONEMAP_PASSWORD=your-onemap-password
```

`DATA_GOV_SG_API_KEY` is optional and only raises data.gov.sg rate limits.
Do not commit `.env`; it is already ignored by Git.

## 4. Install the dependencies

From the repository root:

```powershell
make install
```

This installs the Python backend packages and the frontend npm packages.

On Windows, if the `python` command is not available, use the Python launcher:

```powershell
make PYTHON=py install
```

## 5. Run the app

```powershell
make dev
```

This starts:

- FastAPI backend: <http://127.0.0.1:8000>
- Vite frontend: <http://localhost:5173>

The browser should open automatically. If it does not, open
<http://localhost:5173> manually.

Check that the backend is running:

<http://127.0.0.1:8000/api/v1/health>

Press **Ctrl+C** in the terminal to stop both servers.

## Run without Make (manual)

You do not need GNU Make to run the application. Use two terminals.

### First-time installation

From the repository root:

```powershell
python -m pip install -r backend/requirements.txt
npm --prefix frontend install --no-audit --no-fund
```

If `python` is not recognised on Windows, use the Python launcher:

```powershell
py -m pip install -r backend/requirements.txt
```

### Terminal 1 — backend

```powershell
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If `python` is not recognised:

```powershell
py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 — frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm run dev
```

Then open <http://localhost:5173>. The Vite development server proxies `/api`
requests to the backend at <http://127.0.0.1:8000>.

Stop each server with **Ctrl+C** in its own terminal.

## Make command reference

Run these from the repository root.

| Command | What it does |
| --- | --- |
| `make help` | List all available targets |
| `make install` | Install backend and frontend dependencies |
| `make install-backend` | Install only the Python backend dependencies |
| `make install-frontend` | Install only the frontend npm dependencies |
| `make dev` | Start FastAPI and Vite together |
| `make backend` | Start only FastAPI on port 8000 |
| `make frontend` | Start only Vite on port 5173 |
| `make test` | Run the backend test suite |
| `make test-frontend` | Run the frontend Vitest suite |
| `make build` | Type-check and build the frontend |
| `make benchmark` | Run the SLA benchmark |
| `make amenities` | Rebuild `backend/assets/data/amenities.json` |
| `make clean` | Remove `frontend/dist` and Python caches |

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `make` is not recognised | Reopen the terminal, run `make --version`, and reinstall GNU Make if needed |
| `python` is not recognised | Reopen the terminal, or use `make PYTHON=py install` and `make PYTHON=py dev` |
| `npm` is not recognised | Install Node.js 24 (or 22.22+) and reopen the terminal |
| Port 8000 or 5173 is already in use | Press **Ctrl+C** in the other running instance, then run `make dev` again |
| Address search or routes fail | Check `ONEMAP_EMAIL` and `ONEMAP_PASSWORD` in `.env` |
| Dependencies fail to install | Confirm Python is 3.11+ and Node.js is 24 (or 22.22+), then run `make install` again |

For all backend configuration options, see [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md).
