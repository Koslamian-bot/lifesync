"""
LifeSync — Master Pipeline (main.py)
----------------------------------------
Executes Phase 1 (engine.py) and Phase 2 (planner.py) sequentially.
Enforces a strict block: Phase 2 will not run if Phase 1 fails or exits early.
"""

import subprocess
import sys
import os

# ANSI color helpers for terminal styling matching Phase 1 & 2
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
RED    = "\033[91m"

def header(text):
    width = 62
    print(f"\n{CYAN}{'─' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{CYAN}{'─' * width}{RESET}")

def run_pipeline():
    print(f"\n{BOLD}{CYAN}")
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║        L I F E S Y N C   M A S T E R         ║")
    print("  ║             Pipeline Execution               ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(RESET)

    # ---------------------------------------------------------
    # PHASE 1: Data Extraction (engine.py)
    # ---------------------------------------------------------
    header("INITIATING PHASE 1: ENGINE")
    
    if not os.path.exists("engine.py"):
        print(f"  {RED}✗ Error: engine.py not found in the current directory.{RESET}")
        sys.exit(1)

    try:
        # Run engine.py
        phase1_process = subprocess.run([sys.executable, "engine.py"])
        
        # Check if Phase 1 crashed or was interrupted (e.g., Ctrl+C)
        if phase1_process.returncode != 0:
            print(f"\n  {RED}✗ Phase 1 terminated unexpectedly. Halting pipeline.{RESET}")
            sys.exit(1)
            
        # Strict validation: Ensure the JSON matrix was actually created
        if not os.path.exists("user_profile.json"):
            print(f"\n  {RED}✗ Phase 1 finished, but 'user_profile.json' was not generated. Halting pipeline.{RESET}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n  {RED}✗ Failed to execute Phase 1: {e}{RESET}")
        sys.exit(1)

    print(f"\n  {GREEN}✓ Phase 1 complete. user_profile.json validated.{RESET}")

    # ---------------------------------------------------------
    # PHASE 2: Schedule Generation (planner.py)
    # ---------------------------------------------------------
    header("INITIATING PHASE 2: PLANNER")

    if not os.path.exists("planner.py"):
        print(f"  {RED}✗ Error: planner.py not found in the current directory.{RESET}")
        sys.exit(1)

    try:
        # Run planner.py
        phase2_process = subprocess.run([sys.executable, "planner.py"])
        
        if phase2_process.returncode != 0:
            print(f"\n  {RED}✗ Phase 2 terminated with an error.{RESET}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n  {RED}✗ Failed to execute Phase 2: {e}{RESET}")
        sys.exit(1)

    header("PIPELINE COMPLETE")
    print(f"  {GREEN}✓ LifeSync Engine executed successfully.{RESET}\n")

if __name__ == "__main__":
    run_pipeline()