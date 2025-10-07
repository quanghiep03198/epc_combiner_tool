"""
Advanced DLL Conflict Resolution for Python 313.dll
This script provides comprehensive solutions for resolving Python DLL conflicts
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_dll_isolation_manifest():
    """Create a manifest file to isolate DLL loading"""
    try:
        app_dir = Path(__file__).parent
        manifest_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity 
    version="1.0.0.0" 
    processorArchitecture="amd64" 
    name="EPC Information Combiner" 
    type="win32"/>
  
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges xmlns="urn:schemas-microsoft-com:asm.v3">
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  
  <!-- DLL Redirection and Isolation -->
  <file name="python313.dll" hashalg="SHA1" hash="" />
  <file name="python3.dll" hashalg="SHA1" hash="" />
  
  <!-- Dependency isolation -->
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="amd64"
        publicKeyToken="6595b64144ccf1df"
        language="*"
      />
    </dependentAssembly>
  </dependency>
</assembly>"""

        manifest_file = app_dir / "EPC Information Combiner.exe.manifest"
        manifest_file.write_text(manifest_content, encoding="utf-8")
        print(f"✅ Created DLL isolation manifest: {manifest_file}")

        return True

    except Exception as e:
        print(f"❌ Failed to create manifest: {e}")
        return False


def backup_system_python_dll():
    """Temporarily backup system Python DLL to avoid conflicts"""
    try:
        system_dll_dir = Path("C:/Python313")
        backup_dir = Path(__file__).parent / "system_dll_backup"

        if not system_dll_dir.exists():
            print("✅ No system Python 313 installation found")
            return True

        backup_dir.mkdir(exist_ok=True)

        dll_files = ["python313.dll", "python3.dll"]
        backed_up = []

        for dll_name in dll_files:
            system_dll = system_dll_dir / dll_name
            backup_dll = backup_dir / dll_name

            if system_dll.exists() and not backup_dll.exists():
                print(f"📦 Backing up {dll_name}...")
                shutil.copy2(system_dll, backup_dll)
                backed_up.append(dll_name)

        if backed_up:
            print(f"✅ Backed up system DLLs: {', '.join(backed_up)}")
        else:
            print("✅ System DLLs already backed up or not present")

        return True

    except Exception as e:
        print(f"❌ Failed to backup system DLLs: {e}")
        return False


def create_isolated_startup_script():
    """Create startup script that completely isolates Python environment"""
    try:
        app_dir = Path(__file__).parent
        script_path = app_dir / "start_isolated_python.bat"

        script_content = f"""@echo off
title EPC Information Combiner - Isolated Python Startup

echo 🚀 Starting EPC Information Combiner with Complete Python Isolation
echo =====================================================================

:: Clear ALL Python-related environment variables
set PYTHONPATH=
set PYTHONHOME=
set PYTHON313_DLL=
set PYTHON3_DLL=
set PYTHON_DLL_PATH=
set PYTHONSTARTUP=
set PYTHONEXECUTABLE=

:: Set strict isolation
set PYTHONDONTWRITEBYTECODE=1
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

:: Save original PATH
set ORIGINAL_PATH=%PATH%

:: Create completely isolated PATH without ANY Python directories
set ISOLATED_PATH=
for %%P in ("%PATH:;=" "%") do (
    echo %%~P | findstr /i /c:"python" /c:"conda" /c:"anaconda" /c:"miniconda" >nul || (
        if defined ISOLATED_PATH (
            set "ISOLATED_PATH=!ISOLATED_PATH!;%%~P"
        ) else (
            set "ISOLATED_PATH=%%~P"
        )
    )
)

:: Set the isolated PATH
set PATH=%ISOLATED_PATH%

:: Add only Windows system directories to ensure basic functionality
set PATH=%PATH%;%SystemRoot%\\System32;%SystemRoot%;%SystemRoot%\\System32\\Wbem

echo 🧹 Environment cleaned - Python isolation active
echo 📍 Current directory: %~dp0
echo 🎯 Starting application...

:: Start the application in isolated environment
cd /d "%~dp0"
start "" /wait "EPC Information Combiner.exe"

set EXIT_CODE=%ERRORLEVEL%

:: Restore original PATH
set PATH=%ORIGINAL_PATH%

if %EXIT_CODE% EQU 0 (
    echo ✅ Application exited successfully
) else (
    echo ❌ Application exited with error code: %EXIT_CODE%
    echo 💡 If you see DLL conflicts, try running as administrator
    pause
)

exit /b %EXIT_CODE%"""

        script_path.write_text(script_content, encoding="utf-8")
        print(f"✅ Created isolated startup script: {script_path}")

        return True

    except Exception as e:
        print(f"❌ Failed to create startup script: {e}")
        return False


def test_dll_conflicts():
    """Test for potential DLL conflicts and report findings"""
    try:
        print("🔍 Testing for Python DLL conflicts...")

        conflicts_found = []

        # Check system locations
        system_locations = [
            "C:/Python313/python313.dll",
            "C:/Windows/System32/python313.dll",
            "C:/Windows/SysWOW64/python313.dll",
        ]

        for location in system_locations:
            if Path(location).exists():
                conflicts_found.append(location)

        # Check PATH directories
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for path_dir in path_dirs:
            if "python" in path_dir.lower():
                python_dll = Path(path_dir) / "python313.dll"
                if python_dll.exists():
                    conflicts_found.append(str(python_dll))

        # Check current app directory
        app_dir = Path(__file__).parent
        app_dll = app_dir / "python313.dll"
        if app_dll.exists():
            print(f"📍 Application DLL found: {app_dll}")

        if conflicts_found:
            print(f"⚠️  Found {len(conflicts_found)} potential conflict sources:")
            for conflict in conflicts_found:
                print(f"   - {conflict}")
            return conflicts_found
        else:
            print("✅ No obvious DLL conflicts detected")
            return []

    except Exception as e:
        print(f"❌ Error during conflict testing: {e}")
        return []


def apply_dll_conflict_fixes():
    """Apply all available DLL conflict fixes"""
    print("🔧 Applying DLL Conflict Resolution Measures")
    print("=" * 50)

    fixes = [
        ("System DLL Backup", backup_system_python_dll),
        ("DLL Isolation Manifest", create_dll_isolation_manifest),
        ("Isolated Startup Script", create_isolated_startup_script),
    ]

    results = {}

    for fix_name, fix_function in fixes:
        print(f"\\n🔧 Applying: {fix_name}")
        try:
            results[fix_name] = fix_function()
            status = "✅ Success" if results[fix_name] else "❌ Failed"
            print(f"   Result: {status}")
        except Exception as e:
            results[fix_name] = False
            print(f"   Result: ❌ Error - {e}")

    # Test for conflicts after applying fixes
    print(f"\\n🔍 Testing for remaining conflicts...")
    remaining_conflicts = test_dll_conflicts()

    # Summary
    print(f"\\n📊 Fix Application Summary:")
    print("=" * 30)
    for fix_name, success in results.items():
        status = "✅ Applied" if success else "❌ Failed"
        print(f"{fix_name}: {status}")

    all_applied = all(results.values())
    conflict_status = (
        "✅ Resolved"
        if not remaining_conflicts
        else f"⚠️  {len(remaining_conflicts)} conflicts remain"
    )

    print(
        f"\\nOverall Status: {'✅ All fixes applied' if all_applied else '⚠️  Some fixes failed'}"
    )
    print(f"Conflict Status: {conflict_status}")

    if all_applied and not remaining_conflicts:
        print(f"\\n🎉 DLL Conflict Resolution Complete!")
        print(f"💡 Use 'start_isolated_python.bat' to launch the application")
    elif remaining_conflicts:
        print(f"\\n💡 Recommendations:")
        print(f"   1. Run this script as Administrator for better access")
        print(f"   2. Close all Python applications before running")
        print(f"   3. Use the isolated startup script")
        print(f"   4. Consider uninstalling conflicting Python versions")


if __name__ == "__main__":
    print("EPC Information Combiner - Advanced DLL Conflict Resolution")
    print("=" * 65)
    apply_dll_conflict_fixes()
