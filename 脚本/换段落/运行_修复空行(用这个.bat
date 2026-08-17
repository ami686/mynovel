@echo off
REM 拖拽启动器：把 .md 文件拖到这个 .bat 文件图标上即可运行
REM 它会自动调用同目录下的 fix_md_blank_lines.py 处理你拖过来的文件

python "%~dp0fix_md_blank_lines.py" %*
pause
