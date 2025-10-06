"""
Installation script for EPC Information Combiner updates
This script runs separately to avoid file access issues
"""

import os
import sys
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from helpers.configuration import ConfigService


def wait_for_app_exit(max_wait=30):
    # Wait for main process to exit
    for i in range(max_wait):
        try:
            # Check if main app process is still running
            if os.name == "nt":  # Windows
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq EPC Information Combiner.exe"],
                    capture_output=True,
                    text=True,
                )
                if "EPC Information Combiner.exe" not in result.stdout:
                    break
            time.sleep(1)
        except:
            pass

    # Additional wait to ensure all file handles are closed
    time.sleep(3)
    print("Application appears to have closed")


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
                for attempt in range(5):  # Up to 5 attempts
                    try:
                        # Backup existing file if it exists
                        if dst_file.exists():
                            backup_file = backup_path / rel_path
                            backup_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(dst_file, backup_file)

                        # Copy new file
                        shutil.copy2(src_file, dst_file)
                        copied = True
                        success_count += 1
                        break

                    except (PermissionError, OSError) as e:
                        if attempt < 4:  # Not last attempt
                            print(f"Attempt {attempt + 1} failed for {rel_path}: {e}")
                            time.sleep(2)  # Wait before retry
                        else:
                            print(f"Failed to copy {rel_path} after all attempts: {e}")
                            error_count += 1

                if not copied:
                    print(f"Skipped: {rel_path}")

        print(
            f"Installation completed: {success_count} files copied, {error_count} errors"
        )
        return error_count == 0

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
    """Restart the application"""
    try:
        print("Restarting application...")

        # Wait to ensure all files are released
        print("Waiting for files to be released...")
        time.sleep(3)

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
                    # Start the application with improved flags for reliability
                    process = subprocess.Popen(
                        [str(exe_path)],
                        cwd=str(app_path),
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

    # Wait for main application to close
    wait_for_app_exit()

    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print(f"Backup: {backup_dir}")
    print()

    # Install update
    if install_update(source_dir, target_dir, backup_dir):
        print("Update installed successfully!")
        print("Files preserved: app.cfg, .env files, venv directory, user settings")

        # Restart application
        print("Attempting to restart application...")
        restart_success = restart_application(target_dir)

        if restart_success:
            print("Update completed successfully!")
            print("Application has been restarted with the new version.")
        else:
            print("Update completed but application restart failed.")
            print(
                f" Please manually start: {target_dir}\\EPC Information Combiner.exe"
            )
    else:
        print("Update installation failed!")
        print("Please restore from backup and try again")

    print("\n" + "=" * 50)
    print("Update process finished. Press Enter to close this window...")
    input()
    sys.exit(0)


if __name__ == "__main__":
    main()
