"""
Installation script for EPC Information Combiner updates
This script runs separately to avoid file access issues
"""

import os
import sys
import gc
import time
import shutil
import tempfile
import subprocess
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from helpers.configuration import ConfigService
except ImportError:
    # Fallback ConfigService for standalone execution
    class ConfigService:
        @staticmethod
        def get_env(key, default=None):
            return os.environ.get(key, default)

        @staticmethod
        def get_conf(section, key, default=None):
            return default


def check_file_handles(target_dir):
    """Check if any files in target directory are being used by other processes"""
    try:
        target_path = Path(target_dir)
        locked_files = []

        # Try to check common files that might be locked
        critical_files = [
            "EPC Information Combiner.exe",
            "main.exe",
            "python313.dll",
            "python3.dll",
            "*.pyd",
            "*.dll",
        ]

        for pattern in critical_files:
            if "*" in pattern:
                files = list(target_path.glob(pattern))
            else:
                files = (
                    [target_path / pattern] if (target_path / pattern).exists() else []
                )

            for file_path in files:
                if not file_path.exists():
                    continue

                try:
                    # Try to open file in exclusive mode
                    with open(file_path, "r+b") as f:
                        pass
                except (PermissionError, OSError) as e:
                    locked_files.append((str(file_path), str(e)))

        return locked_files

    except Exception as e:
        print(f"Error checking file handles: {e}")
        return []


def force_release_file_handles():
    """Force release file handles by terminating related processes"""
    try:
        print("🔪 Force releasing file handles...")

        # Kill any remaining processes
        process_patterns = [
            "EPC Information Combiner.exe",
            "main.exe",
            "python.exe",
            "pythonw.exe",
        ]

        for pattern in process_patterns:
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", pattern, "/T"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    print(f"✅ Terminated processes: {pattern}")
            except:
                pass

        # Force garbage collection and memory cleanup
        gc.collect()

        # Wait for system to release handles
        time.sleep(5)

        return True

    except Exception as e:
        print(f"❌ Failed to force release handles: {e}")
        return False


def wait_for_file_handles_release(target_dir, max_wait=30):
    """Wait for all file handles to be released"""
    print("🔍 Checking for locked files...")

    for i in range(max_wait):
        locked_files = check_file_handles(target_dir)

        if not locked_files:
            print("✅ All files are available for update")
            return True

        if i == 0:
            print(f"⚠️  Found {len(locked_files)} locked files:")
            for file_path, error in locked_files[:5]:  # Show first 5
                print(f"   - {Path(file_path).name}: {error}")
            if len(locked_files) > 5:
                print(f"   ... and {len(locked_files) - 5} more")

        elif i == max_wait // 2:  # Halfway through, try force release
            print("🔄 Attempting to force release file handles...")
            force_release_file_handles()

        elif i % 10 == 0:
            print(f"Still waiting for file handles to be released... ({i}/{max_wait}s)")

        time.sleep(1)

    # Final attempt with force
    print(f"⚠️  Timeout waiting for file handles, attempting final force release...")
    force_release_file_handles()

    # Check one more time
    time.sleep(3)
    final_locked = check_file_handles(target_dir)

    if not final_locked:
        print("✅ File handles successfully released")
        return True
    else:
        print(f"⚠️  Still have {len(final_locked)} locked files after force release")
        for file_path, error in final_locked[:3]:
            print(f"   - {Path(file_path).name}: {error}")
        return False


def create_isolated_environment():
    """Create completely isolated environment for Python execution to avoid DLL conflicts"""
    try:
        print("🧹 Creating completely isolated Python environment...")

        # Start with a clean environment copy
        new_env = os.environ.copy()

        # Clear ALL Python-related environment variables that might cause conflicts
        env_vars_to_clear = [
            "PYTHONPATH",
            "PYTHONHOME",
            "PYTHON313_DLL",
            "PYTHON3_DLL",
            "PYTHON_DLL_PATH",
            "PYTHONSTARTUP",
            "PYTHONEXECUTABLE",
            "PYTHON312.DLL",
            "PYTHON311.DLL",
            "PYTHON310.DLL",
            "CONDA_DEFAULT_ENV",
            "CONDA_PREFIX",
            "CONDA_PYTHON_EXE",
            "VIRTUAL_ENV",
            "PIPENV_ACTIVE",
        ]

        for var in env_vars_to_clear:
            if var in new_env:
                print(f"🧹 Clearing environment variable: {var}")
                del new_env[var]

        # Set strict isolation environment
        app_dir = Path(__file__).parent.parent
        new_env["PYTHONDONTWRITEBYTECODE"] = "1"  # Don't create .pyc files
        new_env["PYTHONIOENCODING"] = "utf-8"  # Ensure consistent encoding
        new_env["PYTHONUNBUFFERED"] = "1"  # Immediate output

        # Create completely isolated PATH without ANY Python directories
        path_dirs = new_env.get("PATH", "").split(os.pathsep)
        isolated_path = []

        print("🔍 Filtering PATH directories for Python installations...")

        for path_dir in path_dirs:
            # Check if directory contains any Python-related indicators
            skip_dir = False
            python_indicators = [
                "python",
                "Python",
                "PYTHON",
                "conda",
                "Conda",
                "CONDA",
                "anaconda",
                "Anaconda",
                "ANACONDA",
                "miniconda",
                "Miniconda",
                "MINICONDA",
                "virtualenv",
                "venv",
                "pipenv",
            ]

            for indicator in python_indicators:
                if indicator in path_dir:
                    # Only keep if it's specifically our app directory
                    if str(app_dir).lower() not in path_dir.lower():
                        print(f"🚫 Filtering Python path: {path_dir}")
                        skip_dir = True
                        break

            if not skip_dir:
                isolated_path.append(path_dir)

        # Ensure essential Windows system directories are present
        essential_paths = [
            str(Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32"),
            str(Path(os.environ.get("SystemRoot", "C:\\Windows"))),
            str(
                Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "Wbem"
            ),
            str(
                Path(os.environ.get("SystemRoot", "C:\\Windows"))
                / "System32"
                / "WindowsPowerShell"
                / "v1.0"
            ),
        ]

        for essential_path in essential_paths:
            if Path(essential_path).exists() and essential_path not in isolated_path:
                isolated_path.append(essential_path)

        new_env["PATH"] = os.pathsep.join(isolated_path)

        print(f"✅ Created completely isolated Python environment")
        print(f"   📁 App directory: {app_dir}")
        print(f"   🛡️  Cleared {len(env_vars_to_clear)} environment variables")
        print(
            f"   🔧 PATH filtered from {len(path_dirs)} to {len(isolated_path)} directories"
        )

        return new_env

    except Exception as e:
        print(f"⚠️  Could not create isolated environment: {e}")
        print("   Using fallback environment...")
        return os.environ.copy()


def is_admin():
    """Check if running with administrator privileges on Windows"""
    try:
        import ctypes

        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin(cmd_args):
    """Try to run the installer with elevated privileges"""
    try:
        if os.name == "nt":  # Windows
            import ctypes

            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                " ".join(f'"{arg}"' for arg in cmd_args),
                None,
                1,
            )
            return True
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
    return False


def create_dll_isolation_manifest(target_dir):
    """Create Windows manifest file for DLL isolation to prevent conflicts"""
    try:
        print("📋 Creating DLL isolation manifest...")

        target_path = Path(target_dir)
        manifest_file = target_path / "EPC Information Combiner.exe.manifest"

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

        manifest_file.write_text(manifest_content, encoding="utf-8")
        print(f"✅ Created DLL isolation manifest: {manifest_file}")

        return True

    except Exception as e:
        print(f"❌ Failed to create manifest: {e}")
        return False


def detect_python_dll_conflicts():
    """Detect potential Python DLL conflicts in the system"""
    conflicts = []

    # Common Python DLL locations to check
    system_paths = [
        os.environ.get("SystemRoot", "C:\\Windows") + "\\System32",
        os.environ.get("SystemRoot", "C:\\Windows") + "\\SysWOW64",
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
    ]

    # Add PATH directories
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    system_paths.extend(path_dirs)

    python_dlls = ["python313.dll", "python312.dll", "python311.dll", "python310.dll"]

    for search_path in system_paths:
        if not search_path or not os.path.exists(search_path):
            continue

        try:
            for dll_name in python_dlls:
                dll_path = Path(search_path) / dll_name
                if dll_path.exists():
                    conflicts.append(str(dll_path))
        except (PermissionError, OSError):
            continue

    return conflicts


def handle_dll_conflict(dll_path, backup_path):
    """Special handling for DLL conflicts using Windows techniques"""
    try:
        dll_file = Path(dll_path)
        if not dll_file.exists():
            return True

        dll_name = dll_file.name.lower()

        # Special handling for Python DLLs
        if dll_name.startswith("python") and dll_name.endswith(".dll"):
            print(f"🐍 Detected Python DLL conflict: {dll_name}")

            # Check for system-wide Python DLL conflicts
            system_conflicts = detect_python_dll_conflicts()
            if system_conflicts:
                print(f"⚠️  Found Python DLLs in system PATH:")
                for conflict in system_conflicts[:5]:  # Show first 5
                    print(f"   - {conflict}")
                print(f"💡 This may cause version conflicts with bundled Python")

        # Method 1: Move and replace
        temp_dll = dll_file.with_suffix(".dll.pending")
        if temp_dll.exists():
            temp_dll.unlink()

        # Try to move the locked DLL to pending deletion
        try:
            dll_file.rename(temp_dll)
            print(f"✅ Moved {dll_file.name} to pending deletion")

            # Schedule for deletion on next reboot if still locked
            if os.name == "nt":
                try:
                    import winreg

                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager",
                        0,
                        winreg.KEY_SET_VALUE,
                    )
                    winreg.SetValueEx(
                        key,
                        "PendingFileRenameOperations",
                        0,
                        winreg.REG_MULTI_SZ,
                        [f"{temp_dll}\x00\x00"],
                    )
                    winreg.CloseKey(key)
                    print(f"Scheduled {dll_file.name} for deletion on reboot")
                except:
                    pass
            return True

        except Exception as e:
            print(f"Could not move DLL {dll_file.name}: {e}")
            return False

    except Exception as e:
        print(f"DLL conflict handler failed: {e}")
        return False


def wait_for_app_exit(max_wait=60):
    """Wait for main application to exit completely, with force kill if needed"""
    print("Waiting for application to close...")

    app_processes = []
    force_kill_needed = False

    # Check only for specific application processes (not generic python.exe)
    process_names = [
        "EPC Information Combiner.exe",
        "main.exe",
    ]

    # Wait for graceful exit
    for i in range(max_wait):
        running_processes = []

        try:
            if os.name == "nt":  # Windows
                for process_name in process_names:
                    result = subprocess.run(
                        ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if process_name in result.stdout:
                        # Extract PID for potential force kill
                        lines = result.stdout.strip().split("\n")
                        for line in lines:
                            if process_name in line:
                                parts = line.split()
                                if len(parts) >= 2:
                                    try:
                                        pid = int(parts[1])
                                        running_processes.append((process_name, pid))
                                    except:
                                        pass

                if not running_processes:
                    break

                if i == 0:
                    print(
                        f"Found running processes: {[p[0] for p in running_processes]}"
                    )
                else:  # Progress update every 10 seconds
                    print(f"\rStill waiting... ({i}/{max_wait}s)", end="", flush=True)

            time.sleep(1)

        except Exception as e:
            print(f"Error checking processes: {e}")
            break

    # If processes are still running after graceful wait, force kill
    if running_processes and i >= max_wait - 1:
        print("⚠️  Application did not close gracefully, attempting force kill...")
        force_kill_needed = True

        current_pid = os.getpid()  # Don't kill ourselves!

        for process_name, pid in running_processes:
            try:
                # Skip current process
                if pid == current_pid:
                    print(f"⏩ Skipping current process (PID: {pid})")
                    continue

                print(f"🔪 Force killing {process_name} (PID: {pid})")
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    timeout=10,
                )
                time.sleep(1)
            except Exception as e:
                print(f"❌ Failed to force kill {process_name}: {e}")

    # Additional comprehensive cleanup (skip Python process cleanup)
    print("🧹 Performing safe cleanup...")
    print("✅ Skipping Python process cleanup to preserve installer")

    # Force garbage collection and memory cleanup
    gc.collect()

    # Extended wait to ensure all file handles are released
    wait_time = 8 if force_kill_needed else 3
    print(f"Waiting {wait_time}s for file handles to be released...")
    time.sleep(wait_time)

    # Final verification
    final_check = False
    try:
        for process_name in process_names:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if process_name in result.stdout:
                print(f"Warning: {process_name} may still be running")
                final_check = True
    except:
        pass

    if not final_check:
        print("✅ Application closed successfully")
        return True
    else:
        print("⚠️  Some processes may still be active - proceeding with caution")
        return False


def install_update(source_dir, target_dir, backup_dir):
    """Install update files from source to target directory"""
    if ConfigService.get_env("ENV") == "development":
        print("Development environment detected, skipping installation.")
        return True
    try:
        print(f"Installing update from: {source_dir}")
        print(f"Target directory: {target_dir}")

        source_path = Path(source_dir)
        target_path = Path(target_dir)
        backup_path = Path(backup_dir)

        if not source_path.exists():
            print(f"Source directory not found: {source_dir}")
            return False

        # Create backup directory if it doesn't exist
        backup_path.mkdir(exist_ok=True)

        success_count = 0
        error_count = 0
        dll_conflicts = []
        critical_failures = []

        # Walk through source directory
        for root, dirs, files in os.walk(source_path):
            # Skip certain directories
            dirs[:] = [
                d
                for d in dirs
                if d not in ["data", "logs", "backup_update", "venv", ".env"]
            ]

            for file in files:
                # Skip certain files to preserve user settings and environment
                skip_files = [
                    "app.log",
                    "app.cfg",
                    ".env",
                    "config.ini",
                ]
                if file in skip_files:
                    print(f"Preserving user file: {file}")
                    continue

                src_file = Path(root) / file
                rel_path = src_file.relative_to(source_path)
                dst_file = target_path / rel_path

                # Create directory if needed
                dst_file.parent.mkdir(parents=True, exist_ok=True)

                # Try to copy file with multiple attempts
                copied = False

                # Special handling for DLL files and executables
                is_critical_file = file.lower().endswith((".dll", ".exe", ".pyd"))
                max_attempts = 10 if is_critical_file else 5
                wait_time = 3 if is_critical_file else 2

                for attempt in range(max_attempts):
                    try:
                        # For critical files, try to release any handles
                        if is_critical_file and attempt > 0:
                            print(
                                f"Attempt {attempt + 1}/{max_attempts} for critical file: {file}"
                            )
                            time.sleep(wait_time)

                            # Force garbage collection
                            import gc

                            gc.collect()

                        # Backup existing file if it exists
                        if dst_file.exists():
                            backup_file = backup_path / rel_path
                            backup_file.parent.mkdir(parents=True, exist_ok=True)

                            # For DLL/EXE files, try special Windows handling
                            if is_critical_file:
                                try:
                                    # Backup first
                                    shutil.copy2(dst_file, backup_file)

                                    # For DLL files, use special conflict handler
                                    if file.lower().endswith(".dll"):
                                        if not handle_dll_conflict(
                                            dst_file, backup_file
                                        ):
                                            # If DLL handler fails, continue to normal retry
                                            raise OSError("DLL conflict handler failed")

                                except Exception as backup_error:
                                    print(f"Backup method failed: {backup_error}")
                                    # Continue to normal copy attempt
                            else:
                                shutil.copy2(dst_file, backup_file)

                        # Copy new file
                        shutil.copy2(src_file, dst_file)
                        copied = True
                        success_count += 1
                        break

                    except (PermissionError, OSError) as e:
                        if attempt < max_attempts - 1:  # Not last attempt
                            print(
                                f"⚠️  Attempt {attempt + 1} failed for {rel_path}: {e}"
                            )

                            # Check if it's a file lock issue
                            error_msg = str(e).lower()
                            is_lock_error = any(
                                keyword in error_msg
                                for keyword in [
                                    "being used by another process",
                                    "access is denied",
                                    "permission denied",
                                    "sharing violation",
                                ]
                            )

                            if is_lock_error:
                                print(f"🔒 File lock detected for {file}")

                                # Try to identify which process is using the file
                                try:
                                    # Force release file handles
                                    force_release_file_handles()
                                except:
                                    pass

                            # For DLL conflicts, try additional strategies
                            if is_critical_file and "python" in file.lower():
                                print(f"🐍 Python DLL conflict detected for {file}")

                                # Try to kill any remaining Python processes
                                try:
                                    subprocess.run(
                                        ["taskkill", "/F", "/IM", "python.exe", "/T"],
                                        capture_output=True,
                                        timeout=10,
                                    )
                                    subprocess.run(
                                        ["taskkill", "/F", "/IM", "python3.exe", "/T"],
                                        capture_output=True,
                                        timeout=10,
                                    )
                                    print(
                                        "🔪 Terminated any remaining Python processes"
                                    )
                                except:
                                    pass

                                time.sleep(wait_time * 3)  # Longer wait for Python DLLs

                                # Force Windows to release file handles
                                try:
                                    import ctypes

                                    ctypes.windll.kernel32.SetProcessWorkingSetSize(
                                        -1, -1, -1
                                    )
                                    gc.collect()
                                    print("🧹 Forced memory cleanup")
                                except:
                                    pass
                        else:
                            print(f"Failed to copy {rel_path} after all attempts: {e}")
                            error_count += 1

                            # Track specific conflict types
                            if is_critical_file:
                                if file.lower().endswith(".dll"):
                                    dll_conflicts.append(f"{rel_path}: {e}")
                                else:
                                    critical_failures.append(f"{rel_path}: {e}")

                if not copied:
                    print(f"Skipped: {rel_path}")

        # Print summary report
        print(f"\nInstallation Summary:")
        print(f"   Successfully copied: {success_count} files")
        print(f"   Failed to copy: {error_count} files")

        if dll_conflicts:
            print(f"   DLL conflicts: {len(dll_conflicts)}")
            for conflict in dll_conflicts:
                print(f"      - {conflict}")

        if critical_failures:
            print(f"Critical file failures: {len(critical_failures)}")
            for failure in critical_failures:
                print(f"      - {failure}")

        # Create DLL isolation manifest for conflict prevention
        try:
            create_dll_isolation_manifest(target_dir)
        except Exception as e:
            print(f"⚠️  Failed to create isolation manifest: {e}")

        # Success if no errors or only non-critical errors
        is_success = error_count == 0 or (
            len(dll_conflicts) == 0 and len(critical_failures) == 0
        )

        if not is_success and dll_conflicts:
            print(f"💡 Recommendation: Restart Windows to complete DLL updates")
            print(f"📋 Some DLL files may be scheduled for update on next reboot")

        return is_success

    except Exception as e:
        print(f"Installation failed: {e}")
        return False


def try_alternative_start(exe_path, app_path):
    """Try alternative method to start application"""
    try:
        print("Trying alternative start method...")
        # Use os.startfile for Windows as fallback
        if os.name == "nt":
            os.startfile(str(exe_path))
            time.sleep(3)
            print("Alternative start method completed")
            return True
        else:
            # For Unix-like systems
            subprocess.Popen([str(exe_path)], cwd=str(app_path))
            time.sleep(2)
            return True
    except Exception as e:
        print(f"Alternative start failed: {e}")
        return False


def restart_application(app_dir):
    """Restart the application with isolated environment"""
    try:
        print("🔄 Restarting application...")

        # Create isolated environment to avoid DLL conflicts
        isolated_env = create_isolated_environment()

        # Check for Python DLL conflicts in the application directory
        app_path = Path(app_dir)
        python_dlls = list(app_path.glob("python*.dll"))
        if python_dlls:
            print(f"🐍 Found Python DLLs in app directory:")
            for dll in python_dlls:
                print(f"   - {dll.name}")

        # Wait to ensure all files are released
        print("⏳ Waiting for files to be released...")
        time.sleep(5)  # Longer wait for DLL conflicts

        app_path = Path(app_dir)
        exe_path = None

        # Find executable
        exe_candidates = ["EPC Information Combiner.exe", "main.exe", "app.exe"]
        print(f"Looking for executable in: {app_path}")

        for exe_name in exe_candidates:
            possible_path = app_path / exe_name
            print(f"Checking: {possible_path}")
            if possible_path.exists():
                exe_path = possible_path
                print(f"Found: {exe_path}")
                break

        if exe_path:
            print(f"Starting application: {exe_path.name}")

            if os.name == "nt":  # Windows
                try:
                    # Start the application with isolated environment and improved flags
                    print(f"🚀 Starting {exe_path.name} with isolated environment...")
                    process = subprocess.Popen(
                        [str(exe_path)],
                        cwd=str(app_path),
                        env=isolated_env,  # Use isolated environment
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                        | subprocess.DETACHED_PROCESS,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        shell=False,
                    )

                    print(f"Started process with PID: {process.pid}")

                    # Wait longer for the process to initialize properly
                    time.sleep(5)

                    # Verify the process is still running
                    poll_result = process.poll()
                    if poll_result is None:  # Process is still running
                        print("Application started successfully!")

                        # Double-check with tasklist with better error handling
                        try:
                            result = subprocess.run(
                                ["tasklist", "/FI", f"IMAGENAME eq {exe_path.name}"],
                                capture_output=True,
                                text=True,
                                timeout=15,
                            )

                            if exe_path.name in result.stdout:
                                print("Application confirmed running!")
                                return True
                            else:
                                # Process started but might not be visible in tasklist yet
                                print("Application started (process active)")
                                return True
                        except subprocess.TimeoutExpired:
                            print(
                                "Application verification timeout, but process started"
                            )
                            return True
                    else:
                        print(f"Application process exited with code: {poll_result}")
                        # Try alternative approach
                        return try_alternative_start(exe_path, app_path)

                except subprocess.TimeoutExpired:
                    print(
                        "Timeout while checking application status, but it may have started"
                    )
                    return True
                except Exception as e:
                    print(f"Error starting application: {e}")
                    return False

            else:  # Unix-like
                subprocess.Popen([str(exe_path)], cwd=str(app_path))
                time.sleep(2)
                print("Application started (Unix)")
                return True
        else:
            print("Could not find executable to restart")
            print(f"Searched for: {exe_candidates}")
            print(f"In directory: {app_path}")
            return False

    except Exception as e:
        print(f"Failed to restart application: {e}")
        return False


def cleanup_backup(backup_dir):
    """Clean up backup directory after successful update"""
    try:
        backup_path = Path(backup_dir)
        if backup_path.exists():
            print("Cleaning up backup directory...")
            shutil.rmtree(backup_path)
            print("Backup directory cleaned up successfully")
            return True
        else:
            print("Backup directory not found, nothing to clean up")
            return True
    except Exception as e:
        print(f"Failed to clean up backup directory: {e}")
        print("You can manually delete the backup folder later")
        return False


def main():
    """Main installation process"""
    if len(sys.argv) != 4:
        print("Usage: install_update.py <source_dir> <target_dir> <backup_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    target_dir = sys.argv[2]
    backup_dir = sys.argv[3]

    print("EPC Information Combiner Update Installer")
    print("=" * 50)

    # Check if we have admin privileges on Windows
    need_admin = False
    if os.name == "nt" and not is_admin():
        print("Running without administrator privileges")
        print("This may cause issues with DLL files and system directories")

    # Wait for main application to close
    if not wait_for_app_exit():
        print("⚠️  Warning: Application may not have closed completely")

    # Wait for file handles to be released
    print("🔍 Checking for file handle conflicts...")
    if not wait_for_file_handles_release(target_dir):
        print("⚠️  Warning: Some files may still be locked")
        print("💡 Update will proceed but may encounter conflicts")

    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print(f"Backup: {backup_dir}")
    print()

    # Install update
    install_success = install_update(source_dir, target_dir, backup_dir)

    # If installation failed and we're not admin, try to elevate
    if not install_success and os.name == "nt" and not is_admin():
        print("Installation failed, attempting to run with elevated privileges...")
        if run_as_admin(sys.argv):
            print("Elevated installer launched. This window will close.")
            sys.exit(0)
        else:
            print("Failed to elevate privileges. Manual installation may be required.")

    if install_success:
        print("Update installed successfully!")
        print("Files preserved: app.cfg, .env files, venv directory, user settings")

        # Restart application
        print("Attempting to restart application...")
        restart_success = restart_application(target_dir)

        if restart_success:
            print("Update completed successfully!")
            print("Application has been restarted with the new version.")

            # Clean up backup directory after successful update and restart
            cleanup_backup(backup_dir)

        else:
            print("Update completed but application restart failed.")
            print(f"Please manually start: {target_dir}\\EPC Information Combiner.exe")
            print("Backup directory kept in case of issues")
    else:
        print("Update installation failed!")
        print("Please restore from backup and try again")
        print("Backup directory preserved for recovery")

    print("\n" + "=" * 50)
    print("Update process finished.")
    sys.exit(0 if install_success else 1)


if __name__ == "__main__":
    main()
