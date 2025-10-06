import os
import json
from typing import Dict
from helpers.resolve_path import resolve_path
from helpers.logger import logger
import requests


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
    try:
        version_file = resolve_path("version.json")
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return VersionInfo(data)
    except Exception as e:
        logger.warning(f"Failed to load version info: {e}")

    # Fallback to default version
    return VersionInfo({"version": "1.0.0", "build_type": "unknown"})


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
