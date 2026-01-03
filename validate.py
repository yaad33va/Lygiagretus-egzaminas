#!/usr/bin/env python3
"""
validate.py - Code quality validation script

Checks both C++ and Python code for quality issues using:
- C++: Basic syntax and style checks
- Python: flake8, pylint (if available)
"""

import os
import sys
import subprocess
from typing import List, Tuple


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        return True
    except FileNotFoundError:
        return False


def run_command(command: List[str], description: str) -> Tuple[bool, str]:
    """
    Run a command and return success status and output.

    Args:
        command: Command and arguments as list
        description: Human-readable description

    Returns:
        Tuple of (success, output_message)
    """
    print(f"\n▶ {description}")
    print(f"  Command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        output = result.stdout + result.stderr

        if result.returncode == 0:
            print("  ✓ Passed")
            return True, output
        else:
            print("  ✗ Failed")
            if output.strip():
                print(f"  Output:\n{output[:500]}")
            return False, output

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False, str(e)


def validate_cpp() -> bool:
    """Validate C++ code."""
    print_header("C++ Code Validation")

    if not os.path.exists("main.cpp"):
        print("✗ main.cpp not found")
        return False

    print("✓ main.cpp found")
    all_passed = True

    # Check if C++ compiler exists
    compilers = ["g++", "clang++", "cl"]
    compiler = None
    for c in compilers:
        if check_command_exists(c):
            compiler = c
            print(f"✓ Found compiler: {compiler}")
            break

    if not compiler:
        print("⚠ No C++ compiler found, skipping compilation check")
        print("  Install g++, clang++, or Visual Studio")
    else:
        # Try to compile (syntax check)
        compile_cmd = [
            compiler,
            "-std=c++14",
            "-Wall",
            "-Wextra",
            "-fsyntax-only",
            "main.cpp"
        ]

        if compiler == "cl":
            compile_cmd = [compiler, "/Zs", "/EHsc", "main.cpp"]

        success, _ = run_command(
            compile_cmd,
            "Checking C++ syntax and warnings"
        )
        all_passed = all_passed and success

    # Check for clang-tidy
    if check_command_exists("clang-tidy"):
        success, _ = run_command(
            ["clang-tidy", "main.cpp", "--"],
            "Running clang-tidy"
        )
        all_passed = all_passed and success
    else:
        print("\n⚠ clang-tidy not found (optional)")
        print("  Install: apt-get install clang-tidy (Linux)")
        print("          brew install llvm (macOS)")

    return all_passed


def validate_python() -> bool:
    """Validate Python code."""
    print_header("Python Code Validation")

    python_files = ["worker.py", "generate_data.py"]
    found_files = [f for f in python_files if os.path.exists(f)]

    if not found_files:
        print("✗ No Python files found")
        return False

    print(f"✓ Found {len(found_files)} Python file(s):")
    for f in found_files:
        print(f"  - {f}")

    all_passed = True

    # Check syntax with Python
    for pyfile in found_files:
        success, _ = run_command(
            [sys.executable, "-m", "py_compile", pyfile],
            f"Checking syntax of {pyfile}"
        )
        all_passed = all_passed and success

    # Check with flake8
    if check_command_exists("flake8"):
        for pyfile in found_files:
            success, _ = run_command(
                ["flake8", "--max-line-length=100", pyfile],
                f"Running flake8 on {pyfile}"
            )
            all_passed = all_passed and success
    else:
        print("\n⚠ flake8 not found (recommended)")
        print("  Install: pip install flake8")

    # Check with pylint
    if check_command_exists("pylint"):
        for pyfile in found_files:
            success, _ = run_command(
                ["pylint", "--max-line-length=100", pyfile],
                f"Running pylint on {pyfile}"
            )
            # Pylint can be very strict, so we just warn
            if not success:
                print("  ⚠ Pylint found issues (warnings only)")
    else:
        print("\n⚠ pylint not found (optional)")
        print("  Install: pip install pylint")

    # Check with mypy
    if check_command_exists("mypy"):
        for pyfile in found_files:
            success, _ = run_command(
                ["mypy", pyfile],
                f"Running mypy on {pyfile}"
            )
            if not success:
                print("  ⚠ mypy found type issues (warnings only)")
    else:
        print("\n⚠ mypy not found (optional)")
        print("  Install: pip install mypy")

    return all_passed


def validate_structure() -> bool:
    """Validate project structure."""
    print_header("Project Structure Validation")

    required_files = {
        "main.cpp": "C++ main program",
        "worker.py": "Python worker program",
        "generate_data.py": "Data generator",
        "README.md": "Documentation",
        "Makefile": "Build system",
    }

    all_present = True
    for filename, description in required_files.items():
        if os.path.exists(filename):
            print(f"✓ {filename:25s} - {description}")
        else:
            print(f"✗ {filename:25s} - {description} (MISSING)")
            all_present = False

    # Check for data files
    data_files = ["data1.json", "data2.json", "data3.json", "data4.json"]
    data_present = sum(1 for f in data_files if os.path.exists(f))

    print(f"\n✓ {data_present}/4 data files present")
    if data_present == 0:
        print("  Run: python3 generate_data.py")

    return all_present


def main():
    """Main validation function."""
    print_header("Food Processing System - Code Quality Validation")

    results = {
        "Structure": validate_structure(),
        "Python": validate_python(),
        "C++": validate_cpp(),
    }

    print_header("Validation Summary")

    for category, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{category:20s}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n" + "=" * 70)
        print("  ✓ All validations passed!")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ⚠ Some validations failed or have warnings")
        print("  Review the output above for details")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
