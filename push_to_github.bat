@echo off
title Push Room 114 to GitHub
cd /d "%~dp0"
set "PATH=C:\Users\VISHNULAL\AppData\Local\MinGit\cmd;%PATH%"

echo ========================================================
echo   Pushing Room 114 Project to GitHub (vishnulalviswalal-boop/malak)
echo ========================================================
echo.

git add .
git commit -m "Update Room 114 Kirana store project"
git branch -M main
git remote set-url origin https://github.com/vishnulalviswalal-boop/malak.git

echo.
echo Pushing to GitHub...
echo (If prompted, sign in with your GitHub account or Personal Access Token)
echo.
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   SUCCESS! Successfully pushed to:
    echo   https://github.com/vishnulalviswalal-boop/malak
    echo ========================================================
) else (
    echo.
    echo Push encountered an error. If prompted for password, use a GitHub Personal Access Token.
)
echo.
pause
