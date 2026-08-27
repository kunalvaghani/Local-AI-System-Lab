@echo off
setlocal EnableExtensions

set "LAB_ROOT=%~dp0"
set "BACKEND_URL=http://127.0.0.1:8765/v1/health"
set "BACKEND_CONTRACT_URL=http://127.0.0.1:8765/v1/tools"
set "FRONTEND_URL=http://127.0.0.1:4173/runtime"
set "FRONTEND_RELEASE_URL=http://127.0.0.1:4173/local-ai-release.json"
set "OLLAMA_URL=http://127.0.0.1:11434/api/version"
set "EXPECTED_FRONTEND_STAGE=27"
set "EXPECTED_FRONTEND_VERSION=0.27.0"
set "RUN_MODE=real"
set "WITH_OLLAMA=0"
set "OPEN_BROWSER=1"
set "SKIP_SETUP=0"
set "FORCE_INSTALL=0"
set "SHOW_HELP=0"
set "OLLAMA_STATE=not requested"

:parse_arguments
if "%~1"=="" goto arguments_parsed
if /I "%~1"=="--stub" set "RUN_MODE=stub"& shift& goto parse_arguments
if /I "%~1"=="--with-ollama" set "WITH_OLLAMA=1"& shift& goto parse_arguments
if /I "%~1"=="--no-browser" set "OPEN_BROWSER=0"& shift& goto parse_arguments
if /I "%~1"=="--skip-setup" set "SKIP_SETUP=1"& shift& goto parse_arguments
if /I "%~1"=="--install" set "FORCE_INSTALL=1"& shift& goto parse_arguments
if /I "%~1"=="--help" set "SHOW_HELP=1"& shift& goto parse_arguments
if /I "%~1"=="-h" set "SHOW_HELP=1"& shift& goto parse_arguments
echo [ERROR] Unknown option: %~1
echo.
call :usage
exit /b 2

:arguments_parsed
if "%SHOW_HELP%"=="1" (
    call :usage
    exit /b 0
)

cd /d "%LAB_ROOT%" || (
    echo [ERROR] Could not enter the repository directory: %LAB_ROOT%
    exit /b 1
)

echo ============================================================
echo  Local AI Systems Lab - Stage 27 setup and launcher
echo ============================================================
echo  Repository: %LAB_ROOT%
echo  Backend mode: %RUN_MODE%
echo  Frontend release: Stage %EXPECTED_FRONTEND_STAGE% / %EXPECTED_FRONTEND_VERSION%
echo.

call :require_command powershell.exe "Windows PowerShell"
if errorlevel 1 exit /b 1
call :require_command python.exe "Python 3.10 or newer"
if errorlevel 1 exit /b 1
call :require_command node.exe "Node.js"
if errorlevel 1 exit /b 1
call :require_command npm.cmd "npm"
if errorlevel 1 exit /b 1

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10 or newer is required.
    python --version
    exit /b 1
)

if "%SKIP_SETUP%"=="1" (
    echo [SETUP] Skipped by --skip-setup.
) else (
    call :setup_runtime
    if errorlevel 1 exit /b 1
    call :setup_frontend
    if errorlevel 1 exit /b 1
)

if "%WITH_OLLAMA%"=="1" (
    call :start_optional_ollama
    if errorlevel 1 exit /b 1
)

call :start_backend
if errorlevel 1 exit /b 1

call :start_frontend
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo  Local AI Systems Lab is ready
echo ============================================================
echo  Website: %FRONTEND_URL%
echo  Backend health: %BACKEND_URL%
echo  Backend mode: %RUN_MODE%
echo  Frontend release: Stage %EXPECTED_FRONTEND_STAGE% / %EXPECTED_FRONTEND_VERSION%
echo  Ollama: %OLLAMA_STATE%
echo.
echo The project API uses its pinned llama.cpp runtime in real mode.
echo Ollama is optional and is not substituted for the measured backend.
echo Close service windows that this launcher opened when you want to stop them.

if "%OPEN_BROWSER%"=="1" start "" "%FRONTEND_URL%"
exit /b 0

:setup_runtime
if /I "%RUN_MODE%"=="stub" (
    echo [SETUP] Stub mode does not require the local model artifacts.
    exit /b 0
)

set "LLAMA_EXE=%LAB_ROOT%tools\llama.cpp\b10566\bin\llama-completion.exe"
set "MODEL_FILE=%LAB_ROOT%models\qwen2.5-1.5b-instruct-q4_k_m\qwen2.5-1.5b-instruct-q4_k_m.gguf"
if exist "%LLAMA_EXE%" if exist "%MODEL_FILE%" (
    echo [SETUP] Pinned llama.cpp executable and Qwen GGUF are present.
    exit /b 0
)

if not exist "%MODEL_FILE%" (
    where hf.exe >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] The Qwen model is missing and the Hugging Face hf CLI is unavailable.
        echo         Install the hf CLI, then run this launcher again.
        exit /b 1
    )
)

echo [SETUP] Installing or verifying the pinned llama.cpp and Qwen artifacts...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LAB_ROOT%scripts\setup_stage2.ps1"
if errorlevel 1 (
    echo [ERROR] Local inference setup failed.
    exit /b 1
)
if not exist "%LLAMA_EXE%" (
    echo [ERROR] Setup completed without the expected llama.cpp executable.
    exit /b 1
)
if not exist "%MODEL_FILE%" (
    echo [ERROR] Setup completed without the expected Qwen model.
    exit /b 1
)
exit /b 0

:setup_frontend
if "%FORCE_INSTALL%"=="1" goto install_frontend
if not exist "%LAB_ROOT%apps\web\node_modules\.bin\vite.cmd" goto install_frontend
pushd "%LAB_ROOT%apps\web" || exit /b 1
call npm.cmd ls --depth=0 >nul 2>&1
set "NPM_TREE_EXIT=%ERRORLEVEL%"
popd
if "%NPM_TREE_EXIT%"=="0" (
    echo [SETUP] Exact frontend dependency tree is already installed.
    exit /b 0
)
echo [SETUP] Frontend dependency tree is missing or inconsistent; a clean install is required.

:install_frontend
call :port_open 4173
if not errorlevel 1 (
    echo [ERROR] A frontend is running on port 4173, so npm ci cannot safely replace its native dependencies.
    echo         Stop that frontend yourself, then rerun this launcher with --install.
    exit /b 1
)

echo [SETUP] Installing the exact locked frontend dependencies...
pushd "%LAB_ROOT%apps\web" || (
    echo [ERROR] Could not enter apps\web.
    exit /b 1
)
call npm.cmd ci
set "NPM_EXIT=%ERRORLEVEL%"
popd
if not "%NPM_EXIT%"=="0" (
    echo [ERROR] npm ci failed with exit code %NPM_EXIT%.
    exit /b 1
)
exit /b 0

:start_optional_ollama
call :url_ready "%OLLAMA_URL%"
if not errorlevel 1 (
    set "OLLAMA_STATE=already running"
    echo [OLLAMA] Reusing the healthy service on 127.0.0.1:11434.
    exit /b 0
)

set "OLLAMA_EXE="
for /f "delims=" %%I in ('where ollama.exe 2^>nul') do if not defined OLLAMA_EXE set "OLLAMA_EXE=%%I"
if not defined OLLAMA_EXE if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not defined OLLAMA_EXE if exist "%ProgramFiles%\Ollama\ollama.exe" set "OLLAMA_EXE=%ProgramFiles%\Ollama\ollama.exe"
if not defined OLLAMA_EXE (
    echo [ERROR] --with-ollama was requested, but ollama.exe was not found.
    exit /b 1
)

call :port_open 11434
if not errorlevel 1 (
    echo [ERROR] Port 11434 is occupied, but its Ollama API is not healthy.
    echo         The launcher will not terminate the process using that port.
    exit /b 1
)

echo [OLLAMA] Starting the optional Ollama service...
start "Local AI - Ollama (optional)" /min "%OLLAMA_EXE%" serve
call :wait_for_url "%OLLAMA_URL%" 45
if errorlevel 1 (
    echo [ERROR] Ollama did not become ready within 45 seconds.
    exit /b 1
)
set "OLLAMA_STATE=started (optional)"
exit /b 0

:start_backend
if /I "%RUN_MODE%"=="stub" (
    set "EXPECTED_RUNTIME=local-ai-systems-lab-stage-15-stub"
) else (
    set "EXPECTED_RUNTIME=local-ai-systems-lab-stage-15"
)

call :url_ready "%BACKEND_URL%"
if not errorlevel 1 (
    call :check_backend_mode
    if errorlevel 1 exit /b 1
    call :check_backend_contract
    if errorlevel 1 exit /b 1
    echo [BACKEND] Reusing the healthy matching API on 127.0.0.1:8765.
    exit /b 0
)

call :port_open 8765
if not errorlevel 1 (
    echo [ERROR] Port 8765 is occupied, but the Local AI API health check failed.
    echo         The launcher will not terminate the process using that port.
    exit /b 1
)

echo [BACKEND] Starting first and waiting for health...
if /I "%RUN_MODE%"=="stub" (
    start "Local AI - Backend (Stage 27 stub)" /min /D "%LAB_ROOT%" cmd.exe /d /k python -m runtime.api_cli --stub --database data/stage27-dev.db
) else (
    start "Local AI - Backend (Stage 27 real llama.cpp)" /min /D "%LAB_ROOT%" cmd.exe /d /k python -m runtime.api_cli
)

call :wait_for_url "%BACKEND_URL%" 120
if errorlevel 1 (
    echo [ERROR] The backend did not become healthy within 120 seconds.
    echo         Inspect the "Local AI - Backend" window for details.
    exit /b 1
)
call :check_backend_mode
if errorlevel 1 exit /b 1
call :check_backend_contract
if errorlevel 1 exit /b 1
echo [BACKEND] Ready.
exit /b 0

:check_backend_mode
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; try { $r=Invoke-RestMethod -Uri '%BACKEND_URL%' -TimeoutSec 3; if ($r.data.runtime_name -eq '%EXPECTED_RUNTIME%') { exit 0 }; Write-Host ('[ERROR] Port 8765 is already serving ' + $r.data.runtime_name + ', but this run requested %EXPECTED_RUNTIME%.'); Write-Host '        Stop that backend yourself or rerun with the matching --stub mode.'; exit 2 } catch { exit 1 }"
exit /b %ERRORLEVEL%

:check_backend_contract
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; try { $r=Invoke-RestMethod -Uri '%BACKEND_CONTRACT_URL%' -TimeoutSec 3; if ($r.data.tools.Count -gt 0 -and $r.data.execution.endpoint -eq '/v1/tools/execute') { exit 0 }; Write-Host '[ERROR] The API is healthy but does not expose the Stage 27 product tool contract.'; Write-Host '        Stop that backend yourself, then rerun this launcher.'; exit 2 } catch { Write-Host '[ERROR] The API is healthy but the Stage 27 product contract check failed.'; Write-Host '        The launcher will not terminate that process. Stop it yourself, then rerun.'; exit 1 }"
exit /b %ERRORLEVEL%

:start_frontend
call :url_ready "%FRONTEND_URL%"
if not errorlevel 1 (
    call :check_frontend_release
    if errorlevel 1 exit /b 1
    echo [FRONTEND] Reusing the matching Stage 27 website on 127.0.0.1:4173.
    exit /b 0
)

call :port_open 4173
if not errorlevel 1 (
    echo [ERROR] Port 4173 is occupied, but the Runtime page is not healthy.
    echo         The launcher will not terminate the process using that port.
    exit /b 1
)

echo [FRONTEND] Backend is healthy; starting Vite now...
start "Local AI - Frontend" /min /D "%LAB_ROOT%apps\web" cmd.exe /d /k call npm.cmd run dev
call :wait_for_url "%FRONTEND_URL%" 90
if errorlevel 1 (
    echo [ERROR] The frontend did not become ready within 90 seconds.
    echo         Inspect the "Local AI - Frontend" window for details.
    exit /b 1
)
call :check_frontend_release
if errorlevel 1 exit /b 1
echo [FRONTEND] Ready.
exit /b 0

:check_frontend_release
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; try { $r=Invoke-RestMethod -Uri '%FRONTEND_RELEASE_URL%' -TimeoutSec 3; if ([int]$r.stage -eq %EXPECTED_FRONTEND_STAGE% -and [string]$r.version -eq '%EXPECTED_FRONTEND_VERSION%') { exit 0 }; Write-Host ('[ERROR] Port 4173 is serving frontend Stage ' + $r.stage + ' / ' + $r.version + ', but this launcher requires Stage %EXPECTED_FRONTEND_STAGE% / %EXPECTED_FRONTEND_VERSION%.'); Write-Host '        Stop that frontend yourself, then rerun this launcher.'; exit 2 } catch { Write-Host '[ERROR] Port 4173 is serving a website without the Stage 27 release marker.'; Write-Host '        The launcher will not terminate that process. Stop it yourself, then rerun.'; exit 1 }"
exit /b %ERRORLEVEL%

:require_command
where %~1 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] %~2 was not found on PATH.
    exit /b 1
)
exit /b 0

:url_ready
powershell.exe -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri '%~1' -TimeoutSec 3; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400) { exit 0 } } catch {}; exit 1" >nul 2>&1
exit /b %ERRORLEVEL%

:wait_for_url
powershell.exe -NoProfile -Command "$deadline=(Get-Date).AddSeconds(%~2); do { try { $r=Invoke-WebRequest -UseBasicParsing -Uri '%~1' -TimeoutSec 3; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400) { exit 0 } } catch {}; Start-Sleep -Milliseconds 500 } while ((Get-Date) -lt $deadline); exit 1" >nul 2>&1
exit /b %ERRORLEVEL%

:port_open
powershell.exe -NoProfile -Command "$c=New-Object Net.Sockets.TcpClient; try { $a=$c.BeginConnect('127.0.0.1',%~1,$null,$null); if (-not $a.AsyncWaitHandle.WaitOne(500)) { exit 1 }; $c.EndConnect($a); exit 0 } catch { exit 1 } finally { $c.Dispose() }" >nul 2>&1
exit /b %ERRORLEVEL%

:usage
echo Usage: setup_and_run.bat [options]
echo.
echo Default behavior:
echo   - verifies or installs the pinned llama.cpp and Qwen GGUF runtime
echo   - installs exact package-lock frontend dependencies when node_modules is missing
echo   - starts optional Ollama, then the backend, and waits for the API contract
echo   - starts the frontend only after the backend is healthy and compatible
echo   - rejects stale or unrelated services without terminating them
echo   - opens http://127.0.0.1:4173/runtime
echo.
echo Options:
echo   --stub          Use the deterministic backend without loading the real model
echo   --with-ollama   Also start Ollama; optional and separate from this backend
echo   --no-browser    Do not open the website automatically
echo   --skip-setup    Skip artifact and npm dependency setup
echo   --install       Run a clean npm ci even when node_modules already exists
echo   --help, -h      Show this help
exit /b 0
