:: filepath: /d:/Workspace/My Projects/epc-combiner-tool/build.bat
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

@echo off
pyinstaller main.py --windowed --noconsole --onedir --contents-directory . --name="EPC Information Combiner" --add-data="icon.ico;." --add-data="assets;assets" --add-data="themes/*.qss;themes" --add-data="repositories/sql;repositories/sql" --icon=icon.ico