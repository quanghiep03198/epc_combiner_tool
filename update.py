"""
Auto-update script for EPC Information Combiner
Downloads and installs the latest version from GitHub releases
"""

import os
import sys
import json
import time
import shutil
import zipfile
import tempfile
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class UpdateManager:
    def __init__(self, owner: str, repo: str, current_version: str):
        self.owner = owner
        self.repo = repo
        self.current_version = current_version.lstrip("v")
        self.api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        self.app_dir = Path(__file__).parent.absolute()
        self.backup_dir = self.app_dir / "backup_update"

    def get_latest_release(self) -> Optional[Dict[Any, Any]]:
        """Get latest release information from GitHub API"""
        try:
            print("🔍 Checking for latest release...")
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data.get("tag_name", "").lstrip("v")

            print(f"📋 Current version: v{self.current_version}")
            print(f"📋 Latest version: v{latest_version}")

            if self._is_newer_version(latest_version):
                return release_data
            else:
                print("✅ You already have the latest version!")
                return None

        except requests.RequestException as e:
            print(f"❌ Failed to check for updates: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

    def _is_newer_version(self, remote_version: str) -> bool:
        """Compare versions (handle pre-release versions properly)"""
        try:
            from packaging import version

            remote_ver = version.parse(remote_version)
            current_ver = version.parse(self.current_version)

            # Consider pre-release versions
            if remote_ver > current_ver:
                return True
            elif remote_ver == current_ver:
                return False
            else:
                return False

        except ImportError:
            # Fallback to simple string comparison if packaging not available
            print("⚠️ Warning: packaging library not available, using simple comparison")
            return remote_version != self.current_version

    def find_portable_asset(self, release_data: Dict[Any, Any]) -> Optional[str]:
        """Find portable ZIP asset download URL"""
        assets = release_data.get("assets", [])

        for asset in assets:
            name = asset.get("name", "").lower()
            if "portable.zip" in name or ("zip" in name and "epc-ic" in name):
                download_url = asset.get("browser_download_url")
                size_mb = asset.get("size", 0) / (1024 * 1024)
                print(f"📦 Found portable asset: {asset.get('name')}")
                print(f"📊 Size: {size_mb:.1f} MB")
                return download_url

        print("❌ No portable ZIP asset found in release")
        return None

    def download_update(self, download_url: str) -> Optional[str]:
        """Download the update file"""
        try:
            temp_dir = tempfile.mkdtemp(prefix="epc_update_")
            temp_file = os.path.join(temp_dir, "update.zip")

            print(f"⬇️ Downloading update...")
            print(f"🔗 URL: {download_url}")

            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(
                                f"\r📥 Downloaded: {percent:.1f}%", end="", flush=True
                            )

            print(f"\n✅ Download completed: {temp_file}")
            return temp_file

        except requests.RequestException as e:
            print(f"❌ Download failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected download error: {e}")
            return None

    def create_backup(self) -> bool:
        """Create backup of current installation"""
        try:
            if self.backup_dir.exists():
                print("🗑️ Removing old backup...")
                shutil.rmtree(self.backup_dir)

            print("💾 Creating backup of current installation...")

            # Copy important files and directories
            self.backup_dir.mkdir(exist_ok=True)

            important_items = [
                "main.py",
                "widgets",
                "helpers",
                "services",
                "repositories",
                "themes",
                "assets",
                "i18n",
                "version.json",
            ]

            # Backup important items (excluding logs and data which may be in use)
            for item in important_items:
                src_path = self.app_dir / item
                if src_path.exists():
                    try:
                        if src_path.is_file():
                            shutil.copy2(src_path, self.backup_dir / item)
                        else:
                            shutil.copytree(
                                src_path, self.backup_dir / item, dirs_exist_ok=True
                            )
                    except Exception as e:
                        print(f"⚠️  Failed to backup {item}: {e}")
                        continue

            # Try to backup data and logs, but don't fail if they're in use
            for optional_item in ["data", "logs"]:
                src_path = self.app_dir / optional_item
                if src_path.exists():
                    try:
                        shutil.copytree(
                            src_path,
                            self.backup_dir / optional_item,
                            dirs_exist_ok=True,
                        )
                        print(f"✅ Backed up {optional_item}")
                    except Exception as e:
                        print(
                            f"⚠️  Could not backup {optional_item} (may be in use): {e}"
                        )
                        # Create empty directory as placeholder
                        (self.backup_dir / optional_item).mkdir(exist_ok=True)

            # Backup important config files that should be preserved
            config_files = [
                "app.cfg",
                ".env",
                ".env.local",
                "config.ini",
                "user_settings.json",
            ]
            for config_file in config_files:
                src_path = self.app_dir / config_file
                if src_path.exists():
                    try:
                        shutil.copy2(src_path, self.backup_dir / config_file)
                        print(f"✅ Backed up config: {config_file}")
                    except Exception as e:
                        print(f"⚠️  Could not backup {config_file}: {e}")

            print("✅ Backup created successfully")
            return True

        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return False

    def extract_and_install(self, zip_file_path: str) -> bool:
        """Extract update and install files"""
        try:
            print("📦 Extracting update...")

            temp_extract_dir = tempfile.mkdtemp(prefix="epc_extract_")

            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(temp_extract_dir)

            # Find the extracted app folder
            extracted_items = os.listdir(temp_extract_dir)
            app_folder = None

            for item in extracted_items:
                item_path = os.path.join(temp_extract_dir, item)
                if os.path.isdir(item_path) and "EPC Information Combiner" in item:
                    app_folder = item_path
                    break

            if not app_folder:
                print("❌ Could not find app folder in extracted files")
                return False

            print(f"📁 Found app folder: {app_folder}")

            # Use separate installer to avoid file access issues
            print("📥 Starting installation process...")

            # Check if install_update.py exists
            installer_script = self.app_dir / "install_update.py"
            if not installer_script.exists():
                print("❌ Installer script not found, using direct method...")
                return self._direct_install(app_folder, zip_file_path, temp_extract_dir)

            # Copy installer to temp directory to avoid conflicts
            temp_installer = Path(temp_extract_dir) / "install_update.py"
            shutil.copy2(installer_script, temp_installer)

            print("� Starting separate installation process...")
            print("   This process will exit to allow file replacement.")

            # Start installer in separate process
            if os.name == "nt":  # Windows
                subprocess.Popen(
                    [
                        sys.executable,
                        str(temp_installer),
                        app_folder,
                        str(self.app_dir),
                        str(self.backup_dir),
                    ],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:  # Unix-like
                subprocess.Popen(
                    [
                        sys.executable,
                        str(temp_installer),
                        app_folder,
                        str(self.app_dir),
                        str(self.backup_dir),
                    ]
                )

            # Exit this process to allow file replacement
            print("✅ Installation started. This process will now exit.")
            sys.exit(0)

        except zipfile.BadZipFile:
            print("❌ Downloaded file is not a valid ZIP archive")
            return False
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False

    def _direct_install(
        self, app_folder: str, zip_file_path: str, temp_extract_dir: str
    ) -> bool:
        """Fallback direct installation method"""
        try:
            print("📥 Installing files directly...")

            # Get list of files to copy
            for root, dirs, files in os.walk(app_folder):
                # Skip certain directories that should not be overwritten
                dirs[:] = [
                    d for d in dirs if d not in ["data", "logs", "backup_update"]
                ]

                for file in files:
                    # Skip certain files
                    if file in ["app.log", "settings.json"]:
                        continue

                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, app_folder)
                    dst_file = self.app_dir / rel_path

                    # Create directory if it doesn't exist
                    dst_file.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file with retry
                    for attempt in range(3):
                        try:
                            shutil.copy2(src_file, dst_file)
                            break
                        except (PermissionError, OSError) as e:
                            if attempt == 2:  # Last attempt
                                print(f"⚠️ Could not update {rel_path}: {e}")
                            else:
                                time.sleep(1)  # Wait before retry

            print("✅ Direct installation completed")

            # Cleanup
            shutil.rmtree(temp_extract_dir)
            os.remove(zip_file_path)

            return True

        except zipfile.BadZipFile:
            print("❌ Downloaded file is not a valid ZIP archive")
            return False
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False

    def restore_backup(self) -> bool:
        """Restore from backup if update fails"""
        try:
            if not self.backup_dir.exists():
                print("❌ No backup found to restore")
                return False

            print("🔄 Restoring from backup...")

            for item in self.backup_dir.iterdir():
                dst_path = self.app_dir / item.name

                # Skip files that are likely in use
                if item.name in ["logs", "data"]:
                    print(f"⚠️  Skipping {item.name} (may be in use)")
                    continue

                try:
                    if dst_path.exists():
                        if dst_path.is_file():
                            # Try to remove file, but continue if it fails
                            try:
                                dst_path.unlink()
                            except (PermissionError, OSError) as e:
                                print(f"⚠️  Cannot remove {dst_path}: {e}")
                                continue
                        else:
                            # Try to remove directory, but continue if it fails
                            try:
                                shutil.rmtree(dst_path)
                            except (PermissionError, OSError) as e:
                                print(f"⚠️  Cannot remove directory {dst_path}: {e}")
                                continue

                    if item.is_file():
                        shutil.copy2(item, dst_path)
                    else:
                        shutil.copytree(item, dst_path, dirs_exist_ok=True)

                except Exception as e:
                    print(f"⚠️  Failed to restore {item.name}: {e}")
                    continue

            print("✅ Backup restored successfully")
            return True

        except Exception as e:
            print(f"❌ Backup restoration failed: {e}")
            return False

    def restart_application(self):
        """Restart the application"""
        try:
            print("🔄 Restarting application...")

            # Find the main executable
            exe_path = None
            for possible_name in [
                "EPC Information Combiner.exe",
                "main.exe",
                "app.exe",
            ]:
                possible_path = self.app_dir / possible_name
                if possible_path.exists():
                    exe_path = possible_path
                    break

            if exe_path:
                print(f"🚀 Starting: {exe_path}")

                # Start the application
                if os.name == "nt":  # Windows
                    subprocess.Popen([str(exe_path)], cwd=str(self.app_dir))
                else:  # Unix-like
                    subprocess.Popen([str(exe_path)], cwd=str(self.app_dir))

                # Exit current process
                sys.exit(0)
            else:
                print("❌ Could not find main executable to restart")
                print("📋 Please manually restart the application")
                input("Press Enter to exit...")
                sys.exit(1)

        except Exception as e:
            print(f"❌ Failed to restart application: {e}")
            print("📋 Please manually restart the application")
            input("Press Enter to exit...")
            sys.exit(1)

    def perform_update(self) -> bool:
        """Perform the complete update process"""
        print("🚀 Starting EPC Information Combiner Update Process")
        print("=" * 50)

        # Get latest release
        release_data = self.get_latest_release()
        if not release_data:
            return False

        # Find download URL
        download_url = self.find_portable_asset(release_data)
        if not download_url:
            return False

        # Create backup
        if not self.create_backup():
            print("❌ Cannot proceed without backup")
            return False

        # Download update
        zip_file = self.download_update(download_url)
        if not zip_file:
            print("❌ Download failed")
            return False

        # Install update
        if not self.extract_and_install(zip_file):
            print("❌ Installation failed, restoring backup...")
            self.restore_backup()
            return False

        print("✅ Update completed successfully!")
        return True


def close_file_handles():
    """Try to close any open file handles that might interfere with update"""
    try:
        import gc
        import logging

        # Force garbage collection
        gc.collect()

        # Close any open logging handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        print("🧹 Closed file handles")
    except Exception as e:
        print(f"⚠️ Could not close all file handles: {e}")


def main():
    """Main entry point"""
    try:
        print("🚀 Starting EPC Information Combiner Update Process...")

        # Try to close any remaining file handles
        close_file_handles()

        # Configuration
        GITHUB_OWNER = "quanghiep03198"
        GITHUB_REPO = "epc_combiner_tool"

        # Get current version
        current_version = "1.0.0"  # Default fallback

        # Try to read from version.json
        version_file = Path("version.json")
        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    version_data = json.load(f)
                    current_version = version_data.get("version", current_version)
                    # Clean up version string - remove extra 'v' prefixes
                    current_version = current_version.lstrip("v")
            except Exception as e:
                print(f"⚠️ Warning: Could not read version.json: {e}")

            # Create update manager
        updater = UpdateManager(GITHUB_OWNER, GITHUB_REPO, current_version)

        print(f"📱 EPC Information Combiner Update Tool")
        print(f"📍 Working directory: {Path.cwd()}")
        print(f"📦 Current version: v{current_version}")
        print("")

        # Perform update
        success = updater.perform_update()

        if success:
            print("\n🎉 Update completed! Restarting application...")
            time.sleep(2)
            updater.restart_application()
        else:
            print("\n❌ Update failed!")
            input("Press Enter to exit...")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
