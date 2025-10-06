import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path


def get_git_info():
    """Get git commit info if available"""
    try:
        commit_hash = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )

        commit_date = (
            subprocess.check_output(
                ["git", "log", "-1", "--format=%ci"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )

        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )

        return {
            "commit_hash": commit_hash,
            "commit_date": commit_date,
            "branch": branch,
        }
    except:
        return {"commit_hash": "unknown", "commit_date": "unknown", "branch": "unknown"}


def update_installer_version(version):
    """Update installer.iss file with new version"""
    installer_file = Path("installer.iss")

    if not installer_file.exists():
        print(f"⚠️  Installer file not found: {installer_file}")
        return False

    try:
        # Read current content
        with open(installer_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find and replace the version line
        import re

        version_pattern = r'(#define MyAppVersion\s+")[^"]*(")'

        # Remove 'v' prefix if present for installer
        clean_version = version[1:] if version.startswith("v") else version

        new_content = re.sub(version_pattern, f"\\g<1>{clean_version}\\g<2>", content)

        # Check if replacement was made
        if new_content == content:
            print(f"⚠️  Version pattern not found in {installer_file}")
            return False

        # Write updated content
        with open(installer_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ Updated installer version to: {clean_version}")
        return True

    except Exception as e:
        print(f"⚠️  Failed to update installer version: {e}")
        return False


def create_version_info(version, build_type="development"):
    """Create version info JSON file"""
    git_info = get_git_info()

    version_info = {
        "version": version,
        "build_type": build_type,
        "build_date": datetime.now().isoformat(),
        "build_timestamp": int(datetime.now().timestamp()),
        "git": git_info,
        "platform": {"system": os.name, "python_version": sys.version},
    }

    # Write to version.json
    version_file = Path("version.json")
    with open(version_file, "w", encoding="utf-8") as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)

    print(f"✅ Created version info: {version_file}")
    print(f"   Version: {version}")
    print(f"   Build Type: {build_type}")
    print(f"   Commit: {git_info['commit_hash']}")

    return version_file


def create_windows_version_info(version):
    """Create Windows version info file for PyInstaller"""
    try:
        # Parse version to tuple (e.g., "v1.2.3-beta" -> (1,2,3,0))
        # Strip 'v' prefix and suffix like -beta, -alpha for Windows version info
        version_without_v = version[1:] if version.startswith("v") else version
        base_version = version_without_v.split("-")[0]
        version_parts = base_version.split(".")
        version_tuple = tuple(int(part) for part in version_parts) + (0,) * (
            4 - len(version_parts)
        )

        version_info_content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'EPC Combiner Tool'),
        StringStruct(u'FileDescription', u'EPC Information Combiner'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'EPC Information Combiner'),
        StringStruct(u'LegalCopyright', u'Copyright © 2024'),
        StringStruct(u'OriginalFilename', u'EPC Information Combiner.exe'),
        StringStruct(u'ProductName', u'EPC Information Combiner'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""

        with open("version_info.txt", "w", encoding="utf-8") as f:
            f.write(version_info_content)

        print(f"✅ Created Windows version info: version_info.txt")
        return Path("version_info.txt")

    except Exception as e:
        print(f"⚠️  Failed to create Windows version info: {e}")
        return None


def clean_build_dirs():
    """Clean build and dist directories"""
    for dir_name in ["build", "dist"]:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name} directory...")
            import shutil

            shutil.rmtree(dir_name)


def run_pyinstaller(version, include_version_file=True):
    """Run PyInstaller with the specified configuration"""

    cmd = [
        "pyinstaller",
        "main.py",
        "--windowed",
        "--noconsole",
        "--onedir",
        "--contents-directory",
        ".",
        "--name=EPC Information Combiner",
        "--add-data=icon.ico;.",
        "--add-data=assets;assets",
        "--add-data=themes;themes",
        "--add-data=repositories/sql;repositories/sql",
        "--add-data=update.py;.",
        "--add-data=update.bat;.",
        "--add-data=install_update.py;.",
        "--icon=icon.ico",
    ]

    # Add version.json if created
    if include_version_file and os.path.exists("version.json"):
        cmd.append("--add-data=version.json;.")

    # Add Windows version info if available
    if os.path.exists("version_info.txt"):
        cmd.append("--version-file=version_info.txt")

    print(f"🔨 Building with PyInstaller...")
    print(
        f"Command: {' '.join(cmd[:3])}...{' '.join(cmd[-3:])}"
    )  # Show abbreviated command
    print("📝 Full command written to build_command.txt for debugging")

    # Write full command to file for debugging
    with open("build_command.txt", "w") as f:
        f.write(" ".join(cmd))

    try:
        # Run without capturing output to see real-time progress
        print("⏳ Running PyInstaller (this may take a few minutes)...")
        result = subprocess.run(cmd, check=True)
        print("✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print(f"❌ Build interrupted by user")
        return False


def main():
    parser = argparse.ArgumentParser(description="Build EPC Information Combiner")
    parser.add_argument(
        "--version",
        required=True,
        help="Version number with v prefix (e.g., v1.2.3, v1.2.3-beta)",
    )
    parser.add_argument(
        "--type",
        choices=["development", "release", "beta"],
        default="development",
        help="Build type (default: development)",
    )
    parser.add_argument(
        "--no-version-file", action="store_true", help="Skip creating version.json file"
    )
    parser.add_argument(
        "--no-clean", action="store_true", help="Skip cleaning build directories"
    )

    args = parser.parse_args()

    print(f"🚀 Building EPC Information Combiner {args.version}")
    print(f"   Build Type: {args.type}")
    print(f"   Working Directory: {os.getcwd()}")

    # Validate version format (must start with 'v' and allow suffixes like -beta, -alpha, etc.)
    if not args.version.startswith("v"):
        print("❌ Version must start with 'v' (e.g., v1.2.3, v1.2.3-beta)")
        sys.exit(1)

    try:
        # Remove 'v' prefix and split on first hyphen to separate base version from suffix
        version_without_v = args.version[1:]  # Remove 'v' prefix
        base_version = version_without_v.split("-")[0]
        version_parts = base_version.split(".")
        if len(version_parts) < 2 or len(version_parts) > 4:
            raise ValueError("Invalid version format")
        for part in version_parts:
            int(part)  # Ensure each part is a number
    except ValueError:
        print(
            "❌ Invalid version format. Use semantic versioning with 'v' prefix (e.g., v1.2.3, v1.2.3-beta)"
        )
        sys.exit(1)

    # Clean build directories
    if not args.no_clean:
        clean_build_dirs()

    # Update installer version (always update regardless of version file option)
    update_installer_version(args.version)

    # Create version info
    include_version_file = not args.no_version_file
    if include_version_file:
        create_version_info(args.version, args.type)
        create_windows_version_info(args.version)

    # Run PyInstaller
    success = run_pyinstaller(args.version, include_version_file)

    if success:
        print(f"\n🎉 Build completed successfully!")
        print(f"📁 Output directory: {os.path.abspath('dist')}")

        # Show build artifacts
        dist_path = Path("dist/EPC Information Combiner")
        if dist_path.exists():
            exe_path = dist_path / "EPC Information Combiner.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📦 Executable: {exe_path} ({size_mb:.1f} MB)")
    else:
        print(f"\n💥 Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
