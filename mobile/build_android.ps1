$ErrorActionPreference = "Stop"
$mobile = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $mobile

$jdk = Get-ChildItem "C:\Program Files\Microsoft\jdk-17*" -Directory -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $jdk) {
    throw "JDK 17 was not found. Install Microsoft OpenJDK 17 first."
}

$gradle = Get-ChildItem "$env:USERPROFILE\.gradle\wrapper\dists\gradle-8.3-all" `
    -Recurse -Filter "gradle.bat" -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $gradle) {
    throw "Gradle 8.3 was not found in the local Gradle cache."
}

$sdk = Join-Path $env:LOCALAPPDATA "Android\Sdk"
if (-not (Test-Path $sdk)) {
    throw "Android SDK not found at $sdk"
}

$env:JAVA_HOME = $jdk.FullName
$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk

Write-Host "1/3  Building YONJIZ debug APK..."
Push-Location $mobile
try {
    & $gradle.FullName assembleDebug --no-daemon --console=plain
    if ($LASTEXITCODE -ne 0) { throw "Gradle build failed." }
} finally {
    Pop-Location
}

$apk = Join-Path $mobile "app\build\outputs\apk\debug\app-debug.apk"
if (-not (Test-Path $apk)) { throw "APK was not produced: $apk" }

Write-Host "2/3  Verifying package..."
& "$sdk\build-tools\34.0.0\aapt2.exe" dump badging $apk | Select-String -Pattern "package:|application-label|sdkVersion|targetSdkVersion|uses-permission" |
    ForEach-Object { Write-Host "     $_" }
& "$sdk\build-tools\34.0.0\apksigner.bat" verify --verbose $apk | Select-Object -First 4 |
    ForEach-Object { Write-Host "     $_" }

$desktopApk = Join-Path ([Environment]::GetFolderPath("Desktop")) "YONJIZ.apk"
Write-Host "3/3  Copying APK to $desktopApk"
Copy-Item -LiteralPath $apk -Destination $desktopApk -Force
Write-Host "Done."
Write-Host "APK: $desktopApk"
Write-Host "Size: $((Get-Item $desktopApk).Length) bytes"
