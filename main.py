"""
BUILD-MATRIX.ai Entry Point Launcher
Run `python main.py` (or `python run.py`) to launch the interactive web application,
or specify `--cli` to run headless blueprint generation.
"""

import sys
import os
import argparse
import subprocess


def run_streamlit_app():
    """Launches the Streamlit Web Application."""
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    print(f"🚀 Starting BUILD-MATRIX.ai Web Application...")
    print(f"📍 App File: {app_path}")
    print(f"🌐 Opening in your web browser (http://localhost:8501)...\n")

    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n[!] BUILD-MATRIX.ai Web Application stopped.")
    except Exception as e:
        print(f"\n[!] Error launching application: {e}")


def run_cli_mode(args):
    """Runs the CLI generator."""
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
    from cli import main as cli_main
    cli_main()



def main():
    parser = argparse.ArgumentParser(
        description="BUILD-MATRIX.ai — Architectural Blueprint & 3D Visualization Generator Launcher"
    )
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface (CLI) batch mode")
    parser.add_argument("--prompt", type=str, help="Design prompt (triggers CLI mode)")
    parser.add_argument("--length", type=float, default=20.0, help="Plot length (X)")
    parser.add_argument("--width", type=float, default=15.0, help="Plot width (Y)")
    parser.add_argument("--height", type=float, default=9.0, help="Max height (Z)")
    parser.add_argument("--floors", type=int, default=2, help="Floor count")
    parser.add_argument("--style", type=str, default="Modern", help="Architectural style")
    parser.add_argument("--output-dir", type=str, default="./output", help="Output directory")

    parsed_args, unknown = parser.parse_known_args()

    # If --cli or --prompt is specified, run CLI mode; otherwise default to interactive Streamlit Web App
    if parsed_args.cli or parsed_args.prompt:
        run_cli_mode(parsed_args)
    else:
        run_streamlit_app()


if __name__ == "__main__":
    main()
