@echo off
setlocal
cd /d "%~dp0"
echo AutoEditor - configurare YouTube pe PC-ul tau
echo Nu trimite chei, tokenuri sau coduri de autorizare in chat.
if not exist "client_secret.json" (
  echo Lipseste client_secret.json. Descarca JSON-ul clientului OAuth Desktop din Google Cloud.
  echo Pune-l langa acest fisier, apoi porneste din nou.
  goto failed
)
where gh >nul 2>&1
if errorlevel 1 (
  echo Instaleaza GitHub CLI de la https://cli.github.com si redeschide acest fisier.
  goto failed
)
set "PYTHON=py -3"
where py >nul 2>&1
if errorlevel 1 set "PYTHON=python"
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
  echo Instaleaza Python 3.10 sau mai nou de la https://www.python.org/downloads/
  goto failed
)
gh auth status --hostname github.com >nul 2>&1
if errorlevel 1 (
  gh auth login --hostname github.com --git-protocol https --web
  if errorlevel 1 goto failed
)
if not exist ".venv-oauth\Scripts\python.exe" (
  %PYTHON% -m venv .venv-oauth
  if errorlevel 1 goto failed
)
".venv-oauth\Scripts\python.exe" -m pip install -r requirements-oauth.txt
if errorlevel 1 goto failed
".venv-oauth\Scripts\python.exe" oauth_setup.py auth --repo iZentric/AutoEditor --enable-upload
if errorlevel 1 goto failed
echo Configurarea s-a terminat. Tokenul a fost trimis direct in GitHub Secrets.
pause
exit /b 0
:failed
echo Configurarea NU este confirmata. Citeste mesajul de mai sus; nu trimite credentiale in chat.
pause
exit /b 1
