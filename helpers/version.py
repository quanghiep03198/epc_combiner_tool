import json
import os
import sys
import time
from datetime import datetime
from typing import Dict

import requests

from helpers.logger import logger
from helpers.resolve_path import resolve_path


def _normalize_version_tag(version: str) -> str:
    if not version:
        return ""
    normalized = str(version).strip()
    if not normalized:
        return ""
    return normalized if normalized.startswith("v") else f"v{normalized}"


def _get_windows_executable_version(executable_path: str) -> str:
    if os.name != "nt" or not executable_path or not os.path.exists(executable_path):
        return ""

    try:
        import ctypes
        from ctypes import wintypes

        size = ctypes.windll.version.GetFileVersionInfoSizeW(executable_path, None)
        if not size:
            return ""

        raw_data = ctypes.create_string_buffer(size)
        ok = ctypes.windll.version.GetFileVersionInfoW(
            executable_path, 0, size, raw_data
        )
        if not ok:
            return ""

        value_ptr = wintypes.LPVOID()
        value_len = wintypes.UINT()

        # Matches StringTable in build script (0409/04B0).
        if ctypes.windll.version.VerQueryValueW(
            raw_data,
            "\\StringFileInfo\\040904B0\\ProductVersion",
            ctypes.byref(value_ptr),
            ctypes.byref(value_len),
        ):
            version = ctypes.wstring_at(value_ptr, value_len.value).rstrip("\x00")
            return version.strip()
    except Exception as e:
        logger.warning(f"Failed to read executable version: {e}")

    return ""


def _sync_version_json_with_installed_app(version_file: str, data: Dict) -> Dict:
    """Sync version.json with installed executable version on app startup."""
    try:
        if not getattr(sys, "frozen", False):
            return data

        runtime_version = _normalize_version_tag(
            _get_windows_executable_version(sys.executable)
        )
        if not runtime_version:
            return data

        current_version = _normalize_version_tag(data.get("version", ""))
        if current_version == runtime_version:
            return data

        updated_data = dict(data)
        updated_data["version"] = runtime_version

        if (
            not updated_data.get("build_type")
            or updated_data.get("build_type") == "unknown"
        ):
            updated_data["build_type"] = "release"

        if (
            not updated_data.get("build_date")
            or updated_data.get("build_date") == "unknown"
        ):
            updated_data["build_date"] = datetime.now().isoformat()

        updated_data["build_timestamp"] = int(time.time())
        updated_data.setdefault(
            "git",
            {"commit_hash": "unknown", "commit_date": "unknown", "branch": "unknown"},
        )
        updated_data.setdefault(
            "platform",
            {"system": os.name, "python_version": sys.version},
        )

        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Synchronized version.json from {current_version or 'unknown'} to {runtime_version}"
        )
        return updated_data

    except Exception as e:
        logger.warning(f"Failed to synchronize version.json: {e}")
        return data


class VersionInfo:
    """Version information container"""

    def __init__(self, data: Dict):
        self.version = data.get("version", "1.0.0")
        self.build_type = data.get("build_type", "development")
        self.build_date = data.get("build_date", "unknown")
        self.build_timestamp = data.get("build_timestamp", 0)
        self.git = data.get("git", {})
        self.platform = data.get("platform", {})

    @property
    def commit_hash(self) -> str:
        return self.git.get("commit_hash", "unknown")

    @property
    def branch(self) -> str:
        return self.git.get("branch", "unknown")

    @property
    def is_development_build(self) -> bool:
        return self.build_type == "development"

    @property
    def is_release_build(self) -> bool:
        return self.build_type == "release"

    @property
    def display_version(self) -> str:
        """Get display version with build type suffix"""
        if self.build_type == "development":
            return f"{self.version}-dev"
        elif self.build_type == "beta":
            return f"{self.version}-beta"
        return self.version

    def __str__(self) -> str:
        return self.display_version


def load_version_info() -> VersionInfo:
    """Load version information from version.json"""
    version_file = resolve_path("version.json")
    data = {"version": "1.0.0", "build_type": "unknown"}

    try:
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                data = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load version info: {e}")

    return VersionInfo(data)


def get_current_version() -> str:
    """Get current version string"""
    return load_version_info().version


def get_display_version() -> str:
    """Get display version string"""
    return load_version_info().display_version


def is_development_environment() -> bool:
    """Check if running in development environment based on .env file"""
    try:
        from helpers.configuration import ConfigService

        env_value = ConfigService.get_env("ENV")
        return env_value == "development"
    except Exception as e:
        logger.warning(f"Failed to check environment: {e}")
        # Fallback: check if main.py exists (source code)
        try:
            main_py = resolve_path("main.py")
            return os.path.exists(main_py)
        except:
            return False


def get_update_directory() -> str:
    """Get appropriate update directory based on environment"""
    if is_development_environment():
        return "dev-update"  # For development - git ignored folder
    else:
        return "."  # For production builds


def fetch_latest_version():
    """
    Fetch latest released version from GitHub repository

    Args:
    owner: Repository owner name
    repo: Repository name

    Returns:
    str: Latest released version (Ex: "v1.0.0")
    """
    url = (
        f"https://api.github.com/repos/quanghiep03198/epc_combiner_tool/releases/latest"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        version = data.get("tag_name", "Unknown")
        return version
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch version: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse version response: {e}")
        return None
    except KeyError as e:
        logger.error(f"Version key not found in response: {e}")
        return None


# Global version info instance
version_info = load_version_info()
