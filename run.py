"""Unified runner for the AgentX Multi-Agent Legal Framework.

Usage:
  python run.py            # Start FastAPI backend server (default)
  python run.py --server   # Start FastAPI backend server on http://localhost:8000
  python run.py --frontend # Start Vite React frontend on http://localhost:5173
  python run.py --all      # Start both Backend and Frontend concurrently
  python run.py --demo     # Run terminal multi-agent legal review demo
  python run.py --test     # Run test suite with pytest
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = (
    ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    if sys.platform == "win32"
    else ROOT_DIR / ".venv" / "bin" / "python"
)

PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True) -> None:
    """Run the FastAPI backend with uvicorn."""
    print("\n=======================================================")
    print(f"  Starting AgentX API Server on http://{host}:{port}")
    print(f"  Docs available at: http://{host}:{port}/docs")
    print("=======================================================\n")

    cmd = [
        PYTHON_EXE,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)
    except KeyboardInterrupt:
        print("\nAgentX server stopped.")


def run_frontend() -> None:
    """Run the Vite frontend development server."""
    frontend_dir = ROOT_DIR / "frontend"
    if not frontend_dir.exists():
        print(f"Error: Frontend directory not found at {frontend_dir}")
        sys.exit(1)

    print("\n=======================================================")
    print("  Starting AgentX Frontend (Vite)")
    print("=======================================================\n")

    # Use npx / npm based on platform
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        subprocess.run([npm_cmd, "run", "dev"], cwd=str(frontend_dir), check=True)
    except KeyboardInterrupt:
        print("\nFrontend dev server stopped.")


def run_all() -> None:
    """Run both backend and frontend concurrently."""
    print("\n=======================================================")
    print("  Starting AgentX Full Stack (Backend + Frontend)")
    print("  Backend:  http://127.0.0.1:8000")
    print("  Frontend: http://localhost:5173")
    print("=======================================================\n")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_dir = ROOT_DIR / "frontend"

    server_proc = subprocess.Popen(
        [
            PYTHON_EXE,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--reload",
        ],
        cwd=str(ROOT_DIR),
    )

    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(frontend_dir),
    )

    try:
        server_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping AgentX full stack...")
        server_proc.terminate()
        frontend_proc.terminate()
        server_proc.wait()
        frontend_proc.wait()
        print("Shutdown complete.")


def run_demo(sample_type: str = "nda") -> None:
    """Run terminal CLI demo."""
    cmd = [PYTHON_EXE, "-m", "app.cli", "demo", "--type", sample_type]
    subprocess.run(cmd, cwd=str(ROOT_DIR))


def run_tests() -> None:
    """Run pytest test suite."""
    print("\nRunning AgentX test suite...\n")
    cmd = [PYTHON_EXE, "-m", "pytest", "-v"]
    subprocess.run(cmd, cwd=str(ROOT_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(description="AgentX Runner")
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run FastAPI backend server (default)",
    )
    parser.add_argument(
        "--frontend",
        action="store_true",
        help="Run Vite frontend development server",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run backend and frontend concurrently",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run terminal multi-agent legal review demo",
    )
    parser.add_argument(
        "--demo-type",
        choices=["nda", "non_compete", "liability"],
        default="nda",
        help="Sample task type for demo",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run full test suite",
    )

    args = parser.parse_args()

    if args.demo:
        run_demo(args.demo_type)
    elif args.frontend:
        run_frontend()
    elif args.all:
        run_all()
    elif args.test:
        run_tests()
    else:
        # Default action is running the backend server
        run_server()


if __name__ == "__main__":
    main()
