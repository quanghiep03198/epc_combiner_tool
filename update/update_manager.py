#!/usr/bin/env python3
"""
Clean Ultimate Update Manager - No ctypes dependencies
Production ready update system for EPC application
"""

import os
import sys
import json
import time
import shutil
import zipfile
import tempfile
import subprocess
import traceback
import configparser
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Callable

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("requests not available - auto-detection features limited")

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available - process management features limited")

try:
    # from helpers.resolve_path import resolve_path
    from PyQt6.QtCore import QObject, QThread, pyqtSignal
    from PyQt6.QtWidgets import (
        QApplication,
        QDialog,
        QVBoxLayout,
        QLabel,
        QProgressBar,
        QTextEdit,
        QPushButton,
        QHBoxLayout,
    )
    from PyQt6.QtGui import QIcon

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

try:
    # Keep explicit imports so PyInstaller can discover these modules.
    from themes.colors import Theme as AppTheme
    from themes.theme_manager import theme_manager as app_theme_manager

    THEME_MANAGER_AVAILABLE = True
except Exception:
    THEME_MANAGER_AVAILABLE = False
    AppTheme = None
    app_theme_manager = None


def _hidden_subprocess_kwargs(extra_creationflags: int = 0) -> Dict[str, Any]:
    """Return subprocess kwargs that keep child console windows hidden on Windows."""
    if os.name != "nt":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0

    return {
        "startupinfo": startupinfo,
        "creationflags": subprocess.CREATE_NO_WINDOW | extra_creationflags,
    }


class SafeLogger:
    """Safe logging system that never fails"""

    _listener: Optional[Callable[[str], None]] = None

    @staticmethod
    def set_listener(listener: Optional[Callable[[str], None]]) -> None:
        SafeLogger._listener = listener

    @staticmethod
    def log(level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] [{level}] {message}"
        print(formatted_msg)

        if SafeLogger._listener:
            try:
                SafeLogger._listener(formatted_msg)
            except Exception:
                pass

        # Try to log to file if possible
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, "update.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        except:
            pass  # Fail silently for logging

    @staticmethod
    def info(message: str):
        SafeLogger.log("INFO", message)

    @staticmethod
    def warning(message: str):
        SafeLogger.log("WARNING", message)

    @staticmethod
    def error(message: str):
        SafeLogger.log("ERROR", message)


class ProcessManager:
    """Manage processes without ctypes dependencies"""

    def __init__(self):
        self.logger = SafeLogger()

    def find_processes_by_name(self, process_names: List[str]) -> List[Dict]:
        """Find processes by name"""
        found_processes = []

        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil not available - using tasklist as fallback")
            return self._find_processes_with_tasklist(process_names)

        try:
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    proc_name = proc.info["name"]
                    for target_name in process_names:
                        if proc_name.lower() == target_name.lower():
                            found_processes.append(
                                {
                                    "pid": proc.info["pid"],
                                    "name": proc_name,
                                    "exe": proc.info.get("exe", "Unknown"),
                                }
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.logger.error(f"Error scanning processes: {e}")

        return found_processes

    def _find_processes_with_tasklist(self, process_names: List[str]) -> List[Dict]:
        """Fallback process detection using Windows tasklist"""
        found_processes = []

        try:
            result = subprocess.run(
                ["tasklist", "/fo", "csv"],
                capture_output=True,
                text=True,
                timeout=10,
                **_hidden_subprocess_kwargs(),
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:  # Skip header
                    for line in lines[1:]:
                        parts = line.replace('"', "").split(",")
                        if len(parts) >= 2:
                            proc_name = parts[0]
                            try:
                                pid = int(parts[1])
                                for target_name in process_names:
                                    if proc_name.lower() == target_name.lower():
                                        found_processes.append(
                                            {
                                                "pid": pid,
                                                "name": proc_name,
                                                "exe": "Unknown",
                                            }
                                        )
                            except ValueError:
                                continue

        except Exception as e:
            self.logger.error(f"Error using tasklist: {e}")

        return found_processes

    def terminate_processes_by_name(self, process_names: List[str]) -> bool:
        """Terminate processes by name"""
        found_processes = self.find_processes_by_name(process_names)

        if not found_processes:
            self.logger.info("No matching processes found")
            return True

        terminated = []

        for proc_info in found_processes:
            pid = proc_info["pid"]
            name = proc_info["name"]

            # Try psutil first
            if PSUTIL_AVAILABLE:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    terminated.append(f"{name} (PID: {pid})")
                    self.logger.info(f"Terminated process: {name} (PID: {pid})")
                    continue
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self.logger.warning(f"Could not terminate {name} with psutil: {e}")

            # Fallback to taskkill
            try:
                result = subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    **_hidden_subprocess_kwargs(),
                )
                if result.returncode == 0:
                    terminated.append(f"{name} (PID: {pid})")
                    self.logger.info(
                        f"Terminated process: {name} (PID: {pid}) using taskkill"
                    )
                else:
                    self.logger.warning(f"taskkill failed for {name}: {result.stderr}")
            except Exception as e:
                self.logger.error(f"Error killing process {name}: {e}")

        if terminated:
            # Wait for processes to exit
            time.sleep(2)
            return True

        return False


class FileReplacer:
    """File replacement without Windows API dependencies"""

    def __init__(self):
        self.logger = SafeLogger()

    def replace_file(
        self, source_path: str, target_path: str, backup_dir: Optional[str] = None
    ) -> bool:
        """Replace file with multiple strategies"""

        # Strategy 1: Direct replacement
        if self._try_direct_replacement(source_path, target_path, backup_dir):
            return True

        # Strategy 2: Rename and replace
        if self._try_rename_replacement(source_path, target_path, backup_dir):
            return True

        # Strategy 3: Force delete and copy
        if self._try_force_replacement(source_path, target_path, backup_dir):
            return True

        # Strategy 4: Robocopy replacement (good for locked files like .ico)
        if self._try_robocopy_replacement(source_path, target_path, backup_dir):
            return True

        # Strategy 5: Schedule replacement on reboot for stubborn locked files
        if self._try_pending_rename_replacement(source_path, target_path):
            return True

        # Strategy 6: Skip file (log and continue)
        self.logger.warning(
            f"Could not replace {os.path.basename(target_path)} - skipping"
        )
        return False

    def _try_direct_replacement(
        self, source_path: str, target_path: str, backup_dir: Optional[str] = None
    ) -> bool:
        """Try direct file replacement"""
        try:
            # Create backup if requested
            if backup_dir and os.path.exists(target_path):
                backup_path = os.path.join(backup_dir, os.path.basename(target_path))
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(target_path, backup_path)

            # Direct replacement
            shutil.copy2(source_path, target_path)
            self.logger.info(
                f"Direct replacement successful: {os.path.basename(target_path)}"
            )
            return True

        except Exception as e:
            self.logger.warning(
                f"Direct replacement failed for {os.path.basename(target_path)}: {e}"
            )
            return False

    def _try_rename_replacement(
        self, source_path: str, target_path: str, backup_dir: Optional[str] = None
    ) -> bool:
        """Try rename-then-replace strategy"""
        try:
            if not os.path.exists(target_path):
                return self._try_direct_replacement(
                    source_path, target_path, backup_dir
                )

            # Rename existing file
            temp_name = target_path + f".old.{int(time.time())}"
            os.rename(target_path, temp_name)

            try:
                # Copy new file
                shutil.copy2(source_path, target_path)

                # Create backup if requested
                if backup_dir:
                    backup_path = os.path.join(
                        backup_dir, os.path.basename(target_path)
                    )
                    os.makedirs(backup_dir, exist_ok=True)
                    shutil.copy2(temp_name, backup_path)

                # Remove old file
                os.remove(temp_name)
                self.logger.info(
                    f"Rename replacement successful: {os.path.basename(target_path)}"
                )
                return True

            except Exception:
                # Restore original file
                try:
                    os.rename(temp_name, target_path)
                except:
                    pass
                raise

        except Exception as e:
            self.logger.warning(
                f"Rename replacement failed for {os.path.basename(target_path)}: {e}"
            )
            return False

    def _try_force_replacement(
        self, source_path: str, target_path: str, backup_dir: Optional[str] = None
    ) -> bool:
        """Try force replacement using system commands"""
        try:
            if not os.path.exists(target_path):
                return self._try_direct_replacement(
                    source_path, target_path, backup_dir
                )

            # Create backup first
            if backup_dir:
                backup_path = os.path.join(backup_dir, os.path.basename(target_path))
                os.makedirs(backup_dir, exist_ok=True)
                try:
                    shutil.copy2(target_path, backup_path)
                except:
                    pass

            # Try to remove readonly attribute and delete
            try:
                os.chmod(target_path, 0o777)
            except:
                pass

            # Force delete with Windows del command
            try:
                subprocess.run(
                    ["del", "/f", "/q", target_path],
                    shell=True,
                    capture_output=True,
                    timeout=5,
                    **_hidden_subprocess_kwargs(),
                )
            except:
                pass

            # Copy new file
            shutil.copy2(source_path, target_path)
            self.logger.info(
                f"Force replacement successful: {os.path.basename(target_path)}"
            )
            return True

        except Exception as e:
            self.logger.warning(
                f"Force replacement failed for {os.path.basename(target_path)}: {e}"
            )
            return False

    def _try_robocopy_replacement(
        self, source_path: str, target_path: str, backup_dir: Optional[str] = None
    ) -> bool:
        """Try replacement using robocopy (effective for locked files like .ico)"""
        try:
            if not os.path.exists(source_path):
                return False

            source_dir = os.path.dirname(source_path)
            target_dir = os.path.dirname(target_path)
            filename = os.path.basename(source_path)

            # Create backup first
            if backup_dir and os.path.exists(target_path):
                os.makedirs(backup_dir, exist_ok=True)
                try:
                    shutil.copy2(
                        target_path,
                        os.path.join(backup_dir, os.path.basename(target_path)),
                    )
                except:
                    pass

            # Use robocopy to force overwrite
            result = subprocess.run(
                [
                    "robocopy",
                    source_dir,
                    target_dir,
                    filename,
                    "/IS",
                    "/IT",
                    "/NFL",
                    "/NDL",
                    "/NJH",
                    "/NJS",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                **_hidden_subprocess_kwargs(),
            )

            # robocopy returns 0-7 for success, 8+ for errors
            if result.returncode < 8 and os.path.exists(target_path):
                self.logger.info(
                    f"Robocopy replacement successful: {os.path.basename(target_path)}"
                )
                return True
            else:
                self.logger.warning(
                    f"Robocopy replacement failed for {os.path.basename(target_path)}: exit code {result.returncode}"
                )
                return False

        except Exception as e:
            self.logger.warning(
                f"Robocopy replacement failed for {os.path.basename(target_path)}: {e}"
            )
            return False

    def _try_pending_rename_replacement(
        self, source_path: str, target_path: str
    ) -> bool:
        """Schedule file replacement on next reboot using MoveFileEx (for stubborn locked files)"""
        try:
            # Copy the new file next to the target with a .pending extension
            pending_path = target_path + ".pending"
            shutil.copy2(source_path, pending_path)

            # Use PowerShell to call MoveFileEx with MOVEFILE_DELAY_UNTIL_REBOOT
            script = f"""
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class FileOps {{
                    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
                    public static extern bool MoveFileEx(string lpExistingFileName, string lpNewFileName, int dwFlags);
                    public const int MOVEFILE_DELAY_UNTIL_REBOOT = 0x4;
                    public const int MOVEFILE_REPLACE_EXISTING = 0x1;
                }}
"@
            [FileOps]::MoveFileEx("{pending_path}", "{target_path}", [FileOps]::MOVEFILE_DELAY_UNTIL_REBOOT -bor [FileOps]::MOVEFILE_REPLACE_EXISTING)
            """

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                capture_output=True,
                text=True,
                timeout=10,
                **_hidden_subprocess_kwargs(),
            )

            if result.returncode == 0:
                self.logger.info(
                    f"Scheduled pending replacement on reboot: {os.path.basename(target_path)}"
                )
                return True
            else:
                # Clean up pending file
                try:
                    os.remove(pending_path)
                except:
                    pass
                self.logger.warning(
                    f"Pending rename failed for {os.path.basename(target_path)}: {result.stderr}"
                )
                return False

        except Exception as e:
            self.logger.warning(
                f"Pending rename failed for {os.path.basename(target_path)}: {e}"
            )
            return False


class UpdateDownloader:
    """Download updates using system tools"""

    def __init__(self):
        self.logger = SafeLogger()

    def download_file(self, url: str, output_path: str, max_retries: int = 3) -> bool:
        """Download file using curl or PowerShell"""

        for attempt in range(max_retries):
            self.logger.info(f"Download attempt {attempt + 1}/{max_retries}: {url}")

            # Prefer in-process download to avoid spawning console windows.
            if self._try_requests_download(url, output_path):
                return True

            # Try curl first (more reliable)
            if self._try_curl_download(url, output_path):
                return True

            # Try PowerShell as fallback
            if self._try_powershell_download(url, output_path):
                return True

            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff

        self.logger.error(f"All download attempts failed for {url}")
        return False

    def _try_curl_download(self, url: str, output_path: str) -> bool:
        """Try downloading with curl"""
        try:
            cmd = [
                "curl",
                "-L",
                "-o",
                output_path,
                url,
                "--connect-timeout",
                "30",
                "--max-time",
                "300",
                "--retry",
                "3",
            ]

            print("Downloading with curl... (43MB file, may take a few minutes)")
            result = subprocess.run(cmd, timeout=180, **_hidden_subprocess_kwargs())

            if result.returncode == 0 and os.path.exists(output_path):
                size = os.path.getsize(output_path)
                self.logger.info(f"Curl download successful: {size} bytes")
                return True
            else:
                self.logger.warning(f"Curl download failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.warning(f"Curl download error: {e}")
            return False

    def _try_powershell_download(self, url: str, output_path: str) -> bool:
        """Try downloading with PowerShell"""
        try:
            script = f"""
            try {{
                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                $wc = New-Object System.Net.WebClient
                $wc.DownloadFile('{url}', '{output_path}')
                exit 0
            }} catch {{
                Write-Error $_.Exception.Message
                exit 1
            }}
            """

            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                **_hidden_subprocess_kwargs(),
            )
            if result.returncode == 0 and os.path.exists(output_path):
                size = os.path.getsize(output_path)
                self.logger.info(f"PowerShell download successful: {size} bytes")
                return True
            else:
                self.logger.warning(f"PowerShell download failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.warning(f"PowerShell download error: {e}")
            return False

    def _try_requests_download(self, url: str, output_path: str) -> bool:
        """Try downloading with requests to avoid spawning console subprocesses."""
        if not REQUESTS_AVAILABLE:
            return False

        try:
            with requests.get(url, stream=True, timeout=(30, 300)) as response:
                response.raise_for_status()
                with open(output_path, "wb") as output_file:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            output_file.write(chunk)

            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                self.logger.info(f"Requests download successful: {size} bytes")
                return True

            return False

        except Exception as e:
            self.logger.warning(f"Requests download error: {e}")
            return False


class CleanUpdateManager:
    """Clean Ultimate Update Manager - No ctypes dependencies"""

    def __init__(self):
        self.logger = SafeLogger()
        self.process_manager = ProcessManager()
        self.file_replacer = FileReplacer()
        self.downloader = UpdateDownloader()

    def perform_complete_update(
        self,
        update_url: str,
        install_dir: str,
        current_version: str = None,
        backup_dir: str = None,
        temp_dir: str = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        force: bool = False,
        silent: bool = False,
        process_names: List[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> bool:
        """
        Perform complete update with all safeguards
        """

        def update_progress(value: int, status: str):
            if progress_callback:
                try:
                    progress_callback(value, status)
                except Exception:
                    pass

        self.logger.info("Starting Clean Update Manager")
        update_progress(2, "Starting update")

        # Setup directories
        if not backup_dir:
            backup_dir = os.path.join(install_dir, f"backup_{int(time.time())}")

        if not temp_dir:
            temp_dir = tempfile.mkdtemp(prefix="epc_update_")

        if not process_names:
            process_names = ["main.exe", "EPC Information Combiner.exe"]

        os.makedirs(backup_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Step 1: Check for updates
            self.logger.info("Step 1: Checking for updates...")
            update_progress(10, "Checking for updates")
            if not force:
                has_update = self.check_for_updates(update_url, current_version)
                if not has_update:
                    self.logger.info("No update needed")
                    update_progress(100, "No update needed")
                    return True

            # Step 2: Download update
            self.logger.info("Step 2: Downloading update...")
            update_progress(20, "Getting update information")
            download_info = self._get_download_info(update_url)
            if not download_info:
                self.logger.error("Could not get download information")
                return False

            download_path = os.path.join(temp_dir, "update.zip")
            download_url = download_info.get("download_url", download_info.get("url"))
            if not download_url:
                self.logger.error("No download URL found")
                return False

            if not self.downloader.download_file(download_url, download_path):
                self.logger.error("Download failed")
                return False
            update_progress(45, "Download completed")

            # Step 3: Extract update
            self.logger.info("Step 3: Extracting update...")
            update_progress(55, "Extracting package")
            extract_dir = os.path.join(temp_dir, "extracted")
            if not self._extract_update(download_path, extract_dir):
                self.logger.error("Extraction failed")
                return False

            # Step 4: Terminate processes
            self.logger.info("Step 4: Terminating processes...")
            update_progress(65, "Closing running application")
            self.process_manager.terminate_processes_by_name(process_names)

            # Step 5: Backup current installation
            self.logger.info("Step 5: Creating backup...")
            update_progress(72, "Creating backup")
            if not self._create_backup(install_dir, backup_dir):
                self.logger.warning("Backup creation failed (continuing anyway)")

            # Step 6: Replace files
            self.logger.info("Step 6: Replacing files...")
            success_count, total_count = self._replace_files(
                extract_dir,
                install_dir,
                backup_dir,
                progress_callback=progress_callback,
                progress_start=75,
                progress_end=95,
            )

            # Step 7: Verify update
            self.logger.info("Step 7: Verifying update...")
            update_progress(97, "Verifying update")
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0

            if success_rate >= 70:  # At least 70% success rate
                self.logger.info(
                    f"Update successful! ({success_count}/{total_count} files, {success_rate:.1f}%)"
                )
                update_progress(100, "Update completed")

                # Cleanup temp files
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

                return True
            else:
                self.logger.error(
                    f"Update failed! ({success_count}/{total_count} files, {success_rate:.1f}%)"
                )
                update_progress(100, "Update failed")

                # Try to restore backup
                if not silent:
                    restore = (
                        input("Restore from backup? (y/N): ").lower().startswith("y")
                    )
                    if restore:
                        self._restore_backup(backup_dir, install_dir)

                return False

        except Exception as e:
            self.logger.error(f"Update failed with error: {e}")
            update_progress(100, "Update failed")
            if not silent:
                print(f"Full traceback:\n{traceback.format_exc()}")
            return False

        finally:
            # Cleanup
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except:
                pass

    def check_for_updates(self, update_url: str, current_version: str = None) -> bool:
        """Check if updates are available"""
        try:
            version_info = self._get_download_info(update_url)
            if not version_info:
                return False

            remote_version = version_info.get("version")
            if not remote_version:
                return True  # Assume update available if no version info

            if current_version and current_version == remote_version:
                self.logger.info(f"Current version {current_version} is up to date")
                return False

            self.logger.info(f"Update available: {current_version} -> {remote_version}")
            return True

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return False

    def _get_download_info(self, update_url: str) -> Optional[Dict]:
        """Get download information from update URL"""
        try:
            if not update_url or not isinstance(update_url, str):
                self.logger.error("Update URL is empty or invalid")
                return None

            if update_url.startswith("file://"):
                # Local file
                file_path = update_url[7:]  # Remove 'file://'
                if file_path.endswith(".json"):
                    with open(file_path, "r") as f:
                        version_data = json.load(f)
                        # Ensure we have a download_url
                        if "download_url" not in version_data:
                            version_data["download_url"] = version_data.get(
                                "url", update_url
                            )
                        return version_data
                else:
                    # Direct zip file
                    return {
                        "url": update_url,
                        "version": "unknown",
                        "download_url": update_url,
                    }
            elif update_url.endswith(".zip"):
                # Direct download URL (from auto-detection)
                self.logger.info("Direct ZIP download URL detected")
                return {
                    "url": update_url,
                    "version": "auto-detected",
                    "download_url": update_url,
                }
            else:
                # Remote URL - try to download version.json
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w+", suffix=".json", delete=False
                )
                temp_file.close()

                if self.downloader.download_file(update_url, temp_file.name):
                    with open(temp_file.name, "r") as f:
                        data = json.load(f)
                        # Ensure we have a download_url
                        if "download_url" not in data:
                            data["download_url"] = data.get("url", update_url)
                    os.unlink(temp_file.name)
                    return data
                else:
                    os.unlink(temp_file.name)
                    # Fallback: treat as direct download
                    self.logger.warning(
                        "Failed to get JSON metadata, treating as direct download"
                    )
                    return {
                        "url": update_url,
                        "version": "unknown",
                        "download_url": update_url,
                    }

        except Exception as e:
            self.logger.error(f"Error getting download info: {e}")
            return None

    def _extract_update(self, zip_path: str, extract_dir: str) -> bool:
        """Extract update package"""
        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(extract_dir)

            extracted_files = list(Path(extract_dir).rglob("*"))
            extracted_files = [f for f in extracted_files if f.is_file()]

            self.logger.info(f"Extracted {len(extracted_files)} files")
            return True

        except Exception as e:
            self.logger.error(f"Extraction error: {e}")
            return False

    def _create_backup(self, install_dir: str, backup_dir: str) -> bool:
        """Create backup of current installation"""
        try:
            files_backed_up = 0

            for root, dirs, files in os.walk(install_dir):
                for file in files:
                    source_path = os.path.join(root, file)
                    rel_path = os.path.relpath(source_path, install_dir)
                    backup_path = os.path.join(backup_dir, rel_path)

                    # Skip backup directory itself
                    if backup_dir in source_path:
                        continue

                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)

                    try:
                        shutil.copy2(source_path, backup_path)
                        files_backed_up += 1
                    except Exception as e:
                        self.logger.warning(f"Could not backup {file}: {e}")

            self.logger.info(f"Backed up {files_backed_up} files to {backup_dir}")
            return files_backed_up > 0

        except Exception as e:
            self.logger.error(f"Backup error: {e}")
            return False

    def _replace_files(
        self,
        source_dir: str,
        target_dir: str,
        backup_dir: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        progress_start: int = 0,
        progress_end: int = 100,
    ) -> Tuple[int, int]:
        """Replace files with comprehensive strategy"""
        success_count = 0
        total_count = 0

        try:
            # Find the actual source directory (skip wrapper folders like "EPC Information Combiner")
            actual_source_dir = self._find_actual_source_dir(source_dir)

            # Get all files to replace
            files_to_replace = []
            for root, dirs, files in os.walk(actual_source_dir):
                for file in files:
                    source_path = os.path.join(root, file)
                    rel_path = os.path.relpath(source_path, actual_source_dir)
                    target_path = os.path.join(target_dir, rel_path)
                    files_to_replace.append((source_path, target_path, rel_path))

            total_count = len(files_to_replace)
            self.logger.info(f"Replacing {total_count} files...")

            # Check if any .ico files need replacing and clear icon cache first
            has_ico_files = any(
                rel_path.lower().endswith(".ico") for _, _, rel_path in files_to_replace
            )
            if has_ico_files:
                self._clear_icon_cache()

            for i, (source_path, target_path, rel_path) in enumerate(files_to_replace):
                self.logger.info(f"[{i+1}/{total_count}] {rel_path}")

                if progress_callback and total_count > 0:
                    progress = progress_start + int(
                        (i / total_count) * (progress_end - progress_start)
                    )
                    try:
                        progress_callback(progress, f"Updating: {rel_path}")
                    except Exception:
                        pass

                # Ensure target directory exists
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                # Try to replace file
                if self.file_replacer.replace_file(
                    source_path, target_path, backup_dir
                ):
                    success_count += 1
                    self.logger.info("   Success")
                else:
                    self.logger.warning("   Skipped")

            if progress_callback:
                try:
                    progress_callback(progress_end, "File replacement completed")
                except Exception:
                    pass

        except Exception as e:
            self.logger.error(f"File replacement error: {e}")

        return success_count, total_count

    def _find_actual_source_dir(self, extract_dir: str) -> str:
        """Find the actual source directory containing the application files"""
        # Check if there's a wrapper folder like "EPC Information Combiner"
        subdirs = [
            d
            for d in os.listdir(extract_dir)
            if os.path.isdir(os.path.join(extract_dir, d))
        ]

        # If there's only one subdirectory, it's likely the wrapper
        if len(subdirs) == 1:
            potential_source = os.path.join(extract_dir, subdirs[0])
            # Check if this directory contains typical app files
            contents = os.listdir(potential_source)
            app_indicators = [".exe", ".dll", "assets", "PyQt6", "repositories"]

            # If we find app indicators, use this as source
            if any(
                any(indicator in item for indicator in app_indicators)
                for item in contents
            ):
                self.logger.info(f"Found application directory: {subdirs[0]}")
                return potential_source

        # Fallback to extract_dir if no wrapper found
        return extract_dir

    def _clear_icon_cache(self):
        """Clear Windows icon cache to release locked .ico files"""
        self.logger.info("Clearing Windows icon cache for .ico file replacement...")
        try:
            # Stop Windows Explorer to release icon cache locks
            subprocess.run(
                ["taskkill", "/f", "/im", "explorer.exe"],
                capture_output=True,
                timeout=10,
            )
            time.sleep(1)

            # Delete icon cache files
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            if local_app_data:
                icon_cache_dir = os.path.join(
                    local_app_data, "Microsoft", "Windows", "Explorer"
                )
                if os.path.exists(icon_cache_dir):
                    for f in os.listdir(icon_cache_dir):
                        if f.startswith("iconcache") or f.startswith("thumbcache"):
                            try:
                                os.remove(os.path.join(icon_cache_dir, f))
                            except:
                                pass

            # Also try the legacy icon cache location
            icon_cache_legacy = os.path.join(local_app_data, "IconCache.db")
            if os.path.exists(icon_cache_legacy):
                try:
                    os.remove(icon_cache_legacy)
                except:
                    pass

            self.logger.info("Icon cache cleared")

        except Exception as e:
            self.logger.warning(f"Could not fully clear icon cache: {e}")

        finally:
            # Always restart Explorer
            try:
                subprocess.Popen(
                    ["explorer.exe"],
                    **_hidden_subprocess_kwargs(subprocess.DETACHED_PROCESS),
                )
                time.sleep(2)
                self.logger.info("Explorer restarted")
            except Exception as e:
                self.logger.warning(f"Could not restart Explorer: {e}")

    def _restore_backup(self, backup_dir: str, install_dir: str) -> bool:
        """Restore from backup"""
        try:
            self.logger.info("Restoring from backup...")

            restored_files = 0
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    backup_path = os.path.join(root, file)
                    rel_path = os.path.relpath(backup_path, backup_dir)
                    target_path = os.path.join(install_dir, rel_path)

                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    try:
                        shutil.copy2(backup_path, target_path)
                        restored_files += 1
                    except Exception as e:
                        self.logger.warning(f"Could not restore {file}: {e}")

            self.logger.info(f"Restored {restored_files} files from backup")
            return restored_files > 0

        except Exception as e:
            self.logger.error(f"Restore error: {e}")
            return False


def load_current_theme_name(install_dir: Optional[str] = None) -> str:
    """Load UI theme from app.cfg with a safe fallback."""
    config_candidates = []
    if install_dir:
        config_candidates.append(os.path.join(install_dir, "app.cfg"))

    config_candidates.append(
        os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../app.cfg"))
    )
    config_candidates.append(os.path.abspath("app.cfg"))

    config_path = next((p for p in config_candidates if os.path.exists(p)), None)
    if not config_path:
        return "dark"

    parser = configparser.ConfigParser()

    try:
        parser.read(config_path, encoding="utf-8")
        return parser.get("UI", "theme", fallback="dark")
    except Exception:
        return "dark"


def _load_theme_manager_from_install_dir(install_dir: str):
    """Best-effort fallback loader for theme modules from installed app directory."""
    colors_path = os.path.join(install_dir, "themes", "colors.py")
    manager_path = os.path.join(install_dir, "themes", "theme_manager.py")

    if not (os.path.exists(colors_path) and os.path.exists(manager_path)):
        return None, None

    if install_dir not in sys.path:
        sys.path.insert(0, install_dir)

    try:
        spec_colors = importlib.util.spec_from_file_location("themes.colors", colors_path)
        module_colors = importlib.util.module_from_spec(spec_colors)
        assert spec_colors and spec_colors.loader
        spec_colors.loader.exec_module(module_colors)

        spec_manager = importlib.util.spec_from_file_location("themes.theme_manager", manager_path)
        module_manager = importlib.util.module_from_spec(spec_manager)
        assert spec_manager and spec_manager.loader
        spec_manager.loader.exec_module(module_manager)

        return module_colors.Theme, module_manager.theme_manager
    except Exception:
        return None, None


def apply_shared_theme(app: "QApplication", install_dir: Optional[str] = None) -> None:
    """Apply the same style system used by the main window."""
    try:
        theme_name = load_current_theme_name(install_dir).lower()

        theme_enum = AppTheme
        theme_manager_obj = app_theme_manager

        if not THEME_MANAGER_AVAILABLE and install_dir:
            theme_enum, theme_manager_obj = _load_theme_manager_from_install_dir(
                install_dir
            )

        if theme_enum is None or theme_manager_obj is None:
            raise RuntimeError("ThemeManager modules are not available")

        theme = theme_enum.DARK
        if theme_name == theme_enum.LIGHT.value:
            theme = theme_enum.LIGHT

        theme_manager_obj.apply_theme(app, theme)
    except Exception as e:
        print(f"Could not apply shared theme: {e}")


def restart_updated_application(install_dir: str) -> bool:
    """Restart the updated application after update completion."""
    # Ensure old app instances are gone before launching the updated process.
    try:
        ProcessManager().terminate_processes_by_name(
            ["main.exe", "EPC Information Combiner.exe"]
        )
    except Exception:
        pass

    candidates = [
        os.path.join(install_dir, "EPC Information Combiner.exe"),
        os.path.join(install_dir, "main.exe"),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            subprocess.Popen(
                [candidate],
                cwd=install_dir,
                **_hidden_subprocess_kwargs(subprocess.CREATE_NEW_PROCESS_GROUP),
            )
            return True

    main_py = os.path.join(install_dir, "main.py")
    if os.path.exists(main_py):
        subprocess.Popen(
            [sys.executable, main_py],
            cwd=install_dir,
            **(_hidden_subprocess_kwargs() if os.name == "nt" else {}),
        )
        return True

    return False


if PYQT_AVAILABLE:

    class UpdateWorker(QObject):
        progress_changed = pyqtSignal(int, str)
        log_message = pyqtSignal(str)
        finished = pyqtSignal(bool)

        def __init__(self, args):
            super().__init__()
            self.args = args

        def run(self):
            updater = CleanUpdateManager()

            def log_listener(message: str):
                self.log_message.emit(message)

            def on_progress(value: int, status: str):
                self.progress_changed.emit(value, status)

            SafeLogger.set_listener(log_listener)
            try:
                success = updater.perform_complete_update(
                    update_url=self.args.update_url,
                    install_dir=self.args.install_dir,
                    current_version=self.args.current_version,
                    backup_dir=self.args.backup_dir,
                    force=self.args.force,
                    silent=True,
                    process_names=self.args.processes,
                    progress_callback=on_progress,
                )
                self.finished.emit(success)
            except Exception as e:
                self.log_message.emit(f"Update error: {e}")
                self.finished.emit(False)
            finally:
                SafeLogger.set_listener(None)


    class UpdateProgressDialog(QDialog):
        def __init__(self, args):
            super().__init__()
            self.args = args
            self.success = False
            self.setWindowTitle("EPC Updater")
            self.setMinimumSize(720, 460)
            self._setup_ui()
            self._start_update_worker()

        def _setup_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(10)

            self.status_label = QLabel("Initializing update...")
            layout.addWidget(self.status_label)

            self.progress_bar = QProgressBar()
            self.progress_bar.setFixedHeight(28)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setValue(0)
            layout.addWidget(self.progress_bar)

            self.log_view = QTextEdit()
            self.log_view.setReadOnly(True)
            self.log_view.setMinimumHeight(280)
            layout.addWidget(self.log_view)

            button_row = QHBoxLayout()
            button_row.addStretch()
            self.ok_button = QPushButton("OK")
            self.ok_button.setEnabled(False)
            self.ok_button.setFixedWidth(100)
            self.ok_button.clicked.connect(self._on_ok_clicked)
            button_row.addWidget(self.ok_button)
            layout.addLayout(button_row)

        def _start_update_worker(self):
            self.thread = QThread(self)
            self.worker = UpdateWorker(self.args)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.progress_changed.connect(self._on_progress_changed)
            self.worker.log_message.connect(self._append_log)
            self.worker.finished.connect(self._on_finished)
            self.worker.finished.connect(self.thread.quit)
            self.thread.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        def _on_progress_changed(self, value: int, status: str):
            self.progress_bar.setValue(max(0, min(100, value)))
            self.status_label.setText(status)

        def _append_log(self, message: str):
            self.log_view.append(message)
            scrollbar = self.log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        def _on_finished(self, success: bool):
            self.success = success
            self.progress_bar.setValue(100)
            if success:
                self.status_label.setText("Update completed. Click OK to restart app.")
                self._append_log("Update completed successfully.")
                self.ok_button.setText("Restart")
            else:
                self.status_label.setText("Update failed. Check logs and close.")
                self._append_log("Update failed.")
                self.ok_button.setText("Close")

            self.ok_button.setEnabled(True)

        def _on_ok_clicked(self):
            if self.success:
                restarted = restart_updated_application(self.args.install_dir)
                if not restarted:
                    self._append_log(
                        "Could not find application executable to restart automatically."
                    )
            self.close()

        def closeEvent(self, event):
            if self.thread.isRunning():
                event.ignore()
                return
            event.accept()

def get_latest_release_info():
    """Auto-detect latest release from GitHub and generate download URL"""
    try:
        if not REQUESTS_AVAILABLE:
            print("requests library not available for auto-detection")
            return None

        # GitHub API endpoint
        api_url = "https://api.github.com/repos/quanghiep03198/epc_combiner_tool/releases/latest"

        print("Checking for latest release...")
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()

        release_data = response.json()
        version = release_data["tag_name"]

        # Generate download URL based on version pattern
        # Pattern: https://github.com/quanghiep03198/epc_combiner_tool/releases/download/{version}/epc-ic-{version}-windows-x64.zip
        download_url = f"https://github.com/quanghiep03198/epc_combiner_tool/releases/download/{version}/epc-ic-{version}-windows-x64.zip"

        print(f"Latest version found: {version}")
        print(f"Generated download URL: {download_url}")

        return {
            "version": version,
            "download_url": download_url,
            "release_data": release_data,
        }

    except Exception as e:
        print(f"Failed to get latest release info: {e}")
        return None


def main():
    """CLI interface for the update manager"""
    import argparse

    parser = argparse.ArgumentParser(description="EPC Clean Update Manager")
    parser.add_argument(
        "--update-url", help="Update URL (optional - will auto-detect if not provided)"
    )
    parser.add_argument("--install-dir", default=".", help="Installation directory")
    parser.add_argument("--current-version", help="Current version")
    parser.add_argument("--force", action="store_true", help="Force update")
    parser.add_argument("--silent", action="store_true", help="Silent mode")
    parser.add_argument("--backup-dir", help="Backup directory")
    parser.add_argument(
        "--processes",
        nargs="*",
        default=["main.exe", "EPC Information Combiner.exe"],
        help="Process names to terminate",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Test auto-detection without downloading"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Show PyQt update window",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Disable PyQt update window",
    )

    args = parser.parse_args()

    # Auto-detect latest release if no URL provided
    update_url = args.update_url
    if not update_url:
        print("No update URL provided, auto-detecting latest release...")
        release_info = get_latest_release_info()
        if release_info:
            update_url = release_info["download_url"]
            if not args.current_version:
                args.current_version = "1.0.0"  # Default current version
            print(f"Using auto-detected URL: {update_url}")
            print(f"Version detected: {release_info['version']}")
            if "published_at" in release_info:
                print(f"Published: {release_info['published_at']}")
        else:
            print("Failed to auto-detect latest release")
            print("Please provide --update-url manually")
            sys.exit(1)

    # If dry-run, just show detection results and exit
    if args.dry_run:
        print("\nDry-run mode - showing detection results only:")
        print(f"   Update URL: {update_url}")
        print(f"   Current Version: {args.current_version}")
        print(f"   Install Directory: {args.install_dir}")
        print("Auto-detection working correctly!")
        return

    # Keep args in sync so GUI worker receives the detected URL.
    args.update_url = update_url

    use_gui = PYQT_AVAILABLE and not args.no_gui and (args.gui or not args.silent)

    if use_gui:
        app = QApplication.instance() or QApplication(sys.argv)
        apply_shared_theme(app, args.install_dir)
        current_file = Path(__file__).resolve()
        icon_path = str(current_file.parent.parent / "./icon.ico")
        app.setWindowIcon(QIcon(icon_path))

        dialog = UpdateProgressDialog(args)
        dialog.exec()

        sys.exit(0 if dialog.success else 1)

    updater = CleanUpdateManager()

    success = updater.perform_complete_update(
        update_url=update_url,
        install_dir=args.install_dir,
        current_version=args.current_version,
        backup_dir=args.backup_dir,
        force=args.force,
        silent=args.silent,
        process_names=args.processes,
    )

    if not args.silent:
        if success:
            print("\nUpdate completed successfully!")
        else:
            print("\nUpdate failed!")

        input("Press Enter to exit...")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
