@echo off
cd /d "%~dp0.."
powershell -ExecutionPolicy Bypass -File "%~dp0kill-zombies.ps1" %*
if errorlevel 1 pause
