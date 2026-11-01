param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $repo ".venv-desktop\Scripts\python.exe"

if (-not (Test-Path $py)) {
    throw "Desktop build environment is missing: $py"
}

Write-Host "1/5  Backing up the current database for the desktop seed..."
New-Item -ItemType Directory -Force (Join-Path $repo "seed") | Out-Null
$seedScript = @'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
source = sqlite3.connect(src)
target = sqlite3.connect(dst)
source.backup(target)
target.close()
source.close()
print(dst)
'@
$seedScript | & $py - "$repo\todo.db" "$repo\seed\todo.db"
if ($LASTEXITCODE -ne 0) { throw "Could not create the desktop seed database." }

Write-Host "2/5  Building YONJIZ.exe..."
Push-Location $repo
try {
    & $py -m PyInstaller --noconfirm --clean YONJIZ.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }
} finally {
    Pop-Location
}

$dist = Join-Path $repo "dist\YONJIZ"
if (-not (Test-Path (Join-Path $dist "YONJIZ.exe"))) {
    throw "Build finished without dist\YONJIZ\YONJIZ.exe"
}

Write-Host "3/5  Smoke-testing the packaged executable..."
$smoke = Start-Process -FilePath (Join-Path $dist "YONJIZ.exe") -ArgumentList "--smoke-test" -WorkingDirectory $dist -PassThru
if (-not $smoke.WaitForExit(25000)) {
    Stop-Process -Id $smoke.Id -Force
    throw "Packaged executable did not start and stop cleanly."
}
if ($smoke.ExitCode -ne 0) {
    throw "Packaged executable exited with code $($smoke.ExitCode)."
}
Write-Host "     Packaged app started and exited cleanly."

if ($SkipInstall) {
    Write-Host "4/5  Installation skipped (-SkipInstall)."
    Write-Host "5/5  Portable build: $dist"
    exit 0
}

Write-Host "4/5  Installing to LocalAppData..."
$install = Join-Path $env:LOCALAPPDATA "Programs\YONJIZ"
if (Test-Path $install) {
    $resolved = (Resolve-Path -LiteralPath $install).Path
    $expected = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA "Programs\YONJIZ"))
    if ($resolved -ne $expected) { throw "Unexpected install path: $resolved" }
    Remove-Item -LiteralPath $install -Recurse -Force
}
New-Item -ItemType Directory -Force $install | Out-Null
Copy-Item -Path (Join-Path $dist "*") -Destination $install -Recurse -Force

$exe = Join-Path $install "YONJIZ.exe"
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "YONJIZ.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($desktopShortcut)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = $install
$shortcut.IconLocation = "$exe,0"
$shortcut.Description = "YONJIZ - offline desktop todo app"
$shortcut.Save()

Write-Host "5/5  Desktop shortcut created: $desktopShortcut"
Write-Host "     Executable: $exe"
Write-Host "     Data folder: $env:LOCALAPPDATA\YONJIZ"
