# build_apk.ps1 — Build the FDSB Android APK with the foreground-service patch.
#
# `flet build apk` regenerates the Flutter project, which wipes the
# flet-android-notifications manifest/gradle patch, so this script:
#   1) runs flet build apk (with the project's usual flags)
#   2) re-applies the patch (flet-android-notifications-patch)
#   3) adds the specialUse FGS subtype property (Play Store requirement)
#   4) rebuilds the APK with flutter (incremental, fast)
#   5) copies the result to build\apk\FDSB-arm64-v8a.apk
#
# Usage:
#   .\build_apk.ps1                                        # default build
#   .\build_apk.ps1 -FletArgs @('build','apk','--arch','x86_64')
#   .\build_apk.ps1 -SkipFletBuild                         # patch + rebuild current build\flutter

param(
    [string[]]$FletArgs = @(
        'build', 'apk',
        '--module-name', 'FDSB',
        '--project', 'FDSB',
        '--product', 'FDSB',
        '--artifact', 'FDSB',
        '--org', 'com.fdsb',
        '--description', 'Free Design Studio Bot - Create and run Discord bots locally',
        '--arch', 'arm64-v8a',
        '--compile-app', '--cleanup-app', '--cleanup-packages',
        '--split-per-abi',
        '--android-adaptive-icon-background', '#1B1F2E',
        '--exclude', 'app_data', '.git', '.hash', 'build', '__pycache__', '*.spec',
        '--android-permissions', 'android.permission.WAKE_LOCK=True',
        '--android-permissions', 'android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS=True',
        '--android-permissions', 'android.permission.POST_NOTIFICATIONS=True',
        '--yes',
        '-o', 'build/apk'
    ),
    [switch]$SkipFletBuild
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

$env:JAVA_HOME = 'C:\Users\NTC\java\17.0.13+11'
$env:PYTHONUTF8 = '1'

$Version = '2.3.1'
$FlutterDir = Join-Path $Root 'build\flutter'
$ManifestPath = Join-Path $FlutterDir 'android\app\src\main\AndroidManifest.xml'
$SourceApk = Join-Path $FlutterDir 'build\app\outputs\flutter-apk\app-arm64-v8a-release.apk'
$DestDir = Join-Path $Root 'build\apk'
$DestApk = Join-Path $DestDir 'FDSB-arm64-v8a.apk'

if (-not $SkipFletBuild) {
    Write-Host '==> flet build apk' -ForegroundColor Cyan
    & flet @FletArgs
    if ($LASTEXITCODE -ne 0) { throw 'flet build apk failed' }
}

Write-Host '==> Patching build\flutter (flet-android-notifications)' -ForegroundColor Cyan
& flet-android-notifications-patch --project-root $FlutterDir
if ($LASTEXITCODE -ne 0) { throw 'patch failed' }

Write-Host '==> Adding specialUse FGS subtype property' -ForegroundColor Cyan
$xml = [IO.File]::ReadAllText($ManifestPath)
if ($xml -notmatch 'PROPERTY_SPECIAL_USE_FGS_SUBTYPE') {
    $pattern = [regex]'(?s)<service android:name="com\.dexterous\.flutterlocalnotifications\.ForegroundService".*?android:foregroundServiceType="specialUse"\s*/>'
    if ($pattern.IsMatch($xml)) {
        $nl = "`r`n"
        $replacement = '<service android:name="com.dexterous.flutterlocalnotifications.ForegroundService"' + $nl +
            '            android:exported="false"' + $nl +
            '            android:foregroundServiceType="specialUse">' + $nl +
            '            <property' + $nl +
            '                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"' + $nl +
            '                android:value="Keeps the user-run Discord bot (FDSB) connected while the app is in the background." />' + $nl +
            '        </service>'
        $xml = $pattern.Replace($xml, $replacement)
        [IO.File]::WriteAllText($ManifestPath, $xml, [Text.Encoding]::UTF8)
        Write-Host '  -> property added'
    } else {
        Write-Host '  -> ForegroundService entry not found; skipping'
    }
} else {
    Write-Host '  -> property already present'
}

Write-Host '==> flutter build apk (reusing patched project)' -ForegroundColor Cyan
$env:SERIOUS_PYTHON_SITE_PACKAGES = Join-Path $Root 'build\site-packages'

$MainDart = Join-Path $FlutterDir 'lib\main.dart'
$mainDartText = [IO.File]::ReadAllText($MainDart)
$changed = $false
if ($mainDartText -match 'showAppBootScreen = bool\.tryParse\("False"') {
    $mainDartText = $mainDartText -replace 'showAppBootScreen = bool\.tryParse\("False"', 'showAppBootScreen = bool.tryParse("True"'
    $changed = $true
}
if ($mainDartText -match 'showAppStartupScreen = bool\.tryParse\("False"') {
    $mainDartText = $mainDartText -replace 'showAppStartupScreen = bool\.tryParse\("False"', 'showAppStartupScreen = bool.tryParse("True"'
    $changed = $true
}
if ($changed) {
    [IO.File]::WriteAllText($MainDart, $mainDartText, [Text.Encoding]::UTF8)
    Write-Host '  -> boot/startup screens enabled'
} else {
    Write-Host '  -> boot/startup screens already enabled'
}

Push-Location -LiteralPath $FlutterDir
try {
    & flutter build apk --build-name $Version --target-platform android-arm64 --split-per-abi
    if ($LASTEXITCODE -ne 0) { throw 'flutter build apk failed' }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $SourceApk)) { throw "APK not found: $SourceApk" }
New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
Copy-Item -LiteralPath $SourceApk -Destination $DestApk -Force

Write-Host "==> Done: $DestApk" -ForegroundColor Green
