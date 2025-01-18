from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but they might need fine-tuning.
build_exe_options = {
    "excludes": [],
    "zip_include_packages": [
        "pyqt6",
        "uhfReaderApi",
        "numpy",
        "pyee",
        "pyqt-toast-notification",
        "python-dotenv",
    ],
}

setup(
    name="EPC CI v1.0.0 beta",
    version="1.0.0",
    description="EPC Information Combinator!",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py", base="gui", shortcut_dir="DesktopFolder", icon="assets/icon.ico"
        )
    ],
)
