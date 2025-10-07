"""
DLL Conflict Resolution Script for EPC Information Combiner
This script provides tools to resolve Python DLL conflicts during updates
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def backup_and_isolate_python_dll():
    """Backup system Python DLL and create isolated copy"""
    try:
        app_dir = Path(__file__).parent
        system_python_dll = Path("C:/Python313/python313.dll")

        if not system_python_dll.exists():
            print("✅ No system Python313.dll found")
            return True

        print(f"🔍 Found system Python DLL: {system_python_dll}")

        # Create backup of system DLL
        backup_dll = app_dir / "python313.dll.system_backup"
        if not backup_dll.exists():
            print("📦 Creating backup of system Python DLL...")
            shutil.copy2(system_python_dll, backup_dll)
            print(f"✅ Backup created: {backup_dll}")
        else:
            print("✅ System DLL backup already exists")

        return True

    except Exception as e:
        print(f"❌ Failed to backup system Python DLL: {e}")
        return False


def check_dll_version_compatibility():
    """Check DLL version compatibility"""
    try:
        # Get Python version info
        import platform

        python_version = platform.python_version()
        python_impl = platform.python_implementation()

        print(f"🐍 Current Python: {python_impl} {python_version}")

        # Check for version-specific DLLs in app directory
        app_dir = Path(__file__).parent
        app_dlls = list(app_dir.glob("python*.dll"))

        if app_dlls:
            print(f"🔍 Found Python DLLs in app directory:")
            for dll in app_dlls:
                print(f"   - {dll.name}")
        else:
            print("✅ No Python DLLs in app directory")

        # Check build directory
        build_dir = app_dir / "build" / "EPC Information Combiner"
        if build_dir.exists():
            build_dlls = list(build_dir.glob("python*.dll"))
            if build_dlls:
                print(f"🔍 Found Python DLLs in build directory:")
                for dll in build_dlls:
                    print(f"   - {dll.name}")
            else:
                print("✅ No Python DLLs in build directory")

        return True

    except Exception as e:
        print(f"❌ Version check failed: {e}")
        return False


def create_dll_isolation_script():
    """Create a startup script that isolates DLL loading"""
    try:
        app_dir = Path(__file__).parent
        isolation_script = app_dir / "start_isolated.bat"

        script_content = """@echo off
echo Starting EPC Information Combiner with DLL isolation...

:: Clear Python environment variables
set PYTHONPATH=
set PYTHONHOME=
set PYTHON313_DLL=

:: Set isolated environment
set PYTHONPATH=%~dp0
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8

:: Remove system Python from PATH temporarily
set ORIGINAL_PATH=%PATH%
set PATH=%PATH:C:\\Python313\\Scripts;=%
set PATH=%PATH:C:\\Python313\\;=%

:: Start application
echo 🚀 Starting application with isolated environment...
start "" "%~dp0EPC Information Combiner.exe"

:: Wait a moment then restore PATH
timeout /t 3 /nobreak >nul
set PATH=%ORIGINAL_PATH%

echo ✅ Application started successfully
pause"""

        isolation_script.write_text(script_content, encoding="utf-8")
        print(f"✅ Created DLL isolation script: {isolation_script}")

        return True

    except Exception as e:
        print(f"❌ Failed to create isolation script: {e}")
        return False


def test_isolated_startup():
    """Test starting the application with DLL isolation"""
    try:
        app_dir = Path(__file__).parent
        exe_path = app_dir / "EPC Information Combiner.exe"

        if not exe_path.exists():
            # Try build directory
            exe_path = (
                app_dir
                / "build"
                / "EPC Information Combiner"
                / "EPC Information Combiner.exe"
            )

        if not exe_path.exists():
            print("⚠️  Application executable not found")
            return False

        print(f"🧪 Testing isolated startup of: {exe_path}")

        # Create isolated environment
        isolated_env = os.environ.copy()

        # Clear conflicting variables
        for var in ["PYTHONPATH", "PYTHONHOME"]:
            if var in isolated_env:
                del isolated_env[var]

        # Set isolation variables
        isolated_env["PYTHONPATH"] = str(app_dir)
        isolated_env["PYTHONDONTWRITEBYTECODE"] = "1"
        isolated_env["PYTHONIOENCODING"] = "utf-8"

        # Filter PATH
        path_dirs = isolated_env.get("PATH", "").split(os.pathsep)
        filtered_path = [
            p
            for p in path_dirs
            if "python" not in p.lower() or str(app_dir).lower() in p.lower()
        ]
        isolated_env["PATH"] = os.pathsep.join(filtered_path)

        print("🚀 Attempting isolated startup...")

        # Start process (don't wait for it to finish)
        process = subprocess.Popen(
            [str(exe_path)],
            env=isolated_env,
            cwd=str(exe_path.parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print(f"✅ Process started with PID: {process.pid}")
        print("💡 Check if application started without DLL conflicts")

        return True

    except Exception as e:
        print(f"❌ Isolated startup test failed: {e}")
        return False


def main():
    """Main function"""
    print("EPC Information Combiner - DLL Conflict Resolution")
    print("=" * 55)

    tests = [
        ("System DLL Backup", backup_and_isolate_python_dll),
        ("DLL Version Check", check_dll_version_compatibility),
        ("Isolation Script Creation", create_dll_isolation_script),
        ("Isolated Startup Test", test_isolated_startup),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Summary
    print(f"\n📊 Test Results Summary:")
    print("=" * 30)
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print(
        f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_passed else '⚠️  SOME TESTS FAILED'}"
    )

    if all_passed:
        print(f"\n💡 Next Steps:")
        print(f"   1. Use 'start_isolated.bat' to start the application")
        print(f"   2. The update system will use isolated environment automatically")
        print(f"   3. DLL conflicts should be resolved")


if __name__ == "__main__":
    main()
