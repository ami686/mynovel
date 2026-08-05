@echo off
chcp 65001 >nul
title Hugo 分类勾选工具

if "%~1"=="" (
  echo.
  echo 用法：把文章的 .md 文件拖到这个 .bat 文件上，松开鼠标即可。
  echo.
  echo 或者直接输入文章的完整路径，回车确认：
  set /p ARTICLE=文章路径: 
) else (
  set ARTICLE=%~1
)

echo.
python "%~dp0category_picker.py" --add "%ARTICLE%"

echo.
pause
