:: filepath: /d:/Workspace/My Projects/epc-combiner-tool/build.bat
@echo off
pyinstaller main.py --windowed --noconsole --onedir --contents-directory . --name="EPC Information Combiner" --add-data="app.cfg;." --add-data="icon.ico;." --add-data="assets;assets" --add-data="themes/*.qss;themes" --add-data="repositories/sql;repositories/sql" --icon=icon.ico