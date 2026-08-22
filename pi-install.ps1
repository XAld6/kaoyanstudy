#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

$PiPackage = "@earendil-works/pi-coding-agent"
$PiCmd = "pi"
# Pi publishes npm-shrinkwrap.json, so the explicit installer/reinstaller can
# bypass npm's release-age gate without reopening transitive dependency ranges.
$NpmMinReleaseAgeArg = "--min-release-age=0"
$NodeMinimum = [version]"22.19.0"
$GitForWindowsLatestReleaseApi = "https://api.github.com/repos/git-for-windows/git/releases/latest"
$PiEsc = [char]27
$PiCr = [char]13

function Write-InstallerTitle {
  if (Test-InstallerAnsiOutput) {
    [Console]::Write("${PiEsc}[1m  Pi Installer${PiEsc}[0m`n${PiEsc}[2m  There are many coding agents, but this one is mine.${PiEsc}[0m`n`n")
  } else {
    Write-Host ""
    Write-Host "  Pi Installer"
    Write-Host "  There are many coding agents, but this one is mine."
    Write-Host ""
  }
}

function Test-InstallerInteractiveOutput {
  return (-not [Console]::IsOutputRedirected) -and ($env:TERM -ne "dumb")
}

function Enable-VirtualTerminalOutput {
  if (-not (Test-InstallerInteractiveOutput)) {
    return $false
  }

  if ($null -ne $script:PiVirtualTerminalEnabled) {
    return $script:PiVirtualTerminalEnabled
  }

  if (-not ("ConsoleMode.NativeMethods" -as [Type])) {
    Add-Type -Namespace ConsoleMode -Name NativeMethods -MemberDefinition @"
[DllImport("kernel32.dll", SetLastError = true)]
public static extern System.IntPtr GetStdHandle(int nStdHandle);

[DllImport("kernel32.dll", SetLastError = true)]
public static extern bool GetConsoleMode(System.IntPtr hConsoleHandle, out uint lpMode);

[DllImport("kernel32.dll", SetLastError = true)]
public static extern bool SetConsoleMode(System.IntPtr hConsoleHandle, uint dwMode);
"@
  }

  $stdOutputHandle = -11
  $enableVirtualTerminalProcessing = 0x0004
  $handle = [ConsoleMode.NativeMethods]::GetStdHandle($stdOutputHandle)
  $mode = [uint32]0
  $script:PiVirtualTerminalEnabled = [ConsoleMode.NativeMethods]::GetConsoleMode($handle, [ref]$mode) -and [ConsoleMode.NativeMethods]::SetConsoleMode($handle, ($mode -bor $enableVirtualTerminalProcessing))
  return $script:PiVirtualTerminalEnabled
}

function Test-InstallerAnsiOutput {
  return Enable-VirtualTerminalOutput
}

function Test-InstallerInteractiveInput {
  return -not [Console]::IsInputRedirected
}

function Test-TerminalSupportsUnicode {
  $locale = "$env:LC_ALL$env:LC_CTYPE$env:LANG"
  if ($locale -match "(?i)utf-?8") {
    return $true
  }

  if ($env:TERM_PROGRAM -in @("Apple_Terminal", "iTerm.app", "vscode", "WezTerm")) {
    return $true
  }

  if ($env:WT_SESSION -or $env:TERMINAL_EMULATOR) {
    return $true
  }

  return $false
}

function Get-SpinnerFrame {
  param([int]$Step)

  switch ($Step % 4) {
    0 { return "-" }
    1 { return "\" }
    2 { return "|" }
    default { return "/" }
  }
}

function Get-InstallLogLines {
  param([string]$LogFile)

  if (Test-Path $LogFile) {
    return Get-Content $LogFile
  }
  return @()
}

function Get-NpmInstallProgressLabel {
  param([string]$LogFile, [string]$CurrentLabel)

  $label = $CurrentLabel
  $metadataCacheCount = 0
  $metadataFetchCount = 0
  $tarballCacheCount = 0
  $tarballFetchCount = 0

  foreach ($line in (Get-InstallLogLines $LogFile)) {
    $line = ($line -split $PiCr)[-1]
    if ($line -like "npm verbose title npm install*") {
      $label = "resolving packages"
    } elseif ($line -match "npm http fetch GET .*https://registry\.npmjs\.org/.*\.tgz") {
      $tarballFetchCount += 1
      $label = "fetching tarballs ($tarballFetchCount)"
    } elseif ($line -match "npm http cache .*@https://registry\.npmjs\.org/.*\.tgz") {
      $tarballCacheCount += 1
      if ($tarballFetchCount -gt 0) {
        $label = "fetching tarballs ($tarballFetchCount)"
      } else {
        $label = "checking tarballs ($tarballCacheCount)"
      }
    } elseif ($line -match "npm http fetch GET .*https://registry\.npmjs\.org/") {
      $metadataFetchCount += 1
      $label = "fetching package metadata ($metadataFetchCount)"
    } elseif ($line -match "npm http cache https://registry\.npmjs\.org/") {
      $metadataCacheCount += 1
      if ($metadataFetchCount -gt 0) {
        $label = "fetching package metadata ($metadataFetchCount)"
      } else {
        $label = "checking cached metadata ($metadataCacheCount)"
      }
    } elseif ($line -like "npm info run *") {
      $rest = $line.Substring("npm info run ".Length)
      $parts = $rest -split " "
      $package = $parts[0]
      $script = if ($parts.Length -gt 1) { $parts[1] } else { "script" }
      $package = $package -replace "@[^@]*$", ""
      if ($line -like "*{ code:*") {
        $label = "finished $script for $package"
      } else {
        $label = "running $script for $package"
      }
    } elseif (($line -like "changed *") -or ($line -like "added *") -or ($line -like "removed *") -or ($line -like "updated *") -or ($line -like "up to date *")) {
      $label = $line
    }
  }

  if ($label.Length -gt 64) {
    $label = $label.Substring(0, 61) + "..."
  }
  return $label
}

function Get-VisibleTextLength {
  param([string]$Text)

  $escapedEsc = [regex]::Escape([string]$PiEsc)
  $visibleText = [regex]::Replace($Text, "${escapedEsc}\[[0-9;?]*[ -/]*[@-~]", "")
  return $visibleText.Length
}

function Write-InstallProgress {
  param([int]$Step, [string]$Frame, [string]$Label, [string]$Title)

  $reset = "${PiEsc}[0m"
  $dim = "${PiEsc}[2m"
  $cyan = "${PiEsc}[36m"
  $red = "${PiEsc}[31m"
  $green = "${PiEsc}[32m"
  $orange = "${PiEsc}[33m"
  $bold = "${PiEsc}[1m"
  $width = 28
  $trail = 8
  $head = $Step % ($width + $trail)
  $bar = ""

  for ($i = 0; $i -lt $width; $i += 1) {
    $age = $head - $i
    if (($age -ge 0) -and ($age -lt $trail)) {
      switch ($age) {
        { $_ -in 0, 1 } { $cell = "${green}#${reset}"; break }
        { $_ -in 2, 3 } { $cell = "${cyan}#${reset}"; break }
        { $_ -in 4, 5 } { $cell = "${red}#${reset}"; break }
        default { $cell = "${orange}#${reset}" }
      }
    } else {
      $cell = "${dim}-${reset}"
    }
    $bar += $cell
  }

  $line = "  ${orange}${Frame}${reset} $bar ${bold}${Title}${reset} $Label"
  $visibleWidth = Get-VisibleTextLength $line
  $lastWidth = [int]$script:PiLastProgressWidth
  $padWidth = [Math]::Max(0, $lastWidth - $visibleWidth)

  [Console]::Write("`r$line" + (" " * $padWidth))
  $script:PiLastProgressWidth = [Math]::Max($lastWidth, $visibleWidth)
}

function Finish-InstallProgress {
  $lastWidth = [int]$script:PiLastProgressWidth
  if ($lastWidth -gt 0) {
    [Console]::Write("`r" + (" " * $lastWidth) + "`r")
  } else {
    [Console]::Write("`r")
  }
  [Console]::Write("${PiEsc}[?25h")
  $script:PiLastProgressWidth = 0
}

function Write-StaticLogo {
  if (Test-InstallerInteractiveOutput) {
    $block = [string][char]0x2588
  } else {
    $block = "#"
  }

  Write-Host ""
  Write-Host ("  " + ($block * 6))
  Write-Host ("  " + ($block * 2) + "  " + ($block * 2))
  Write-Host ("  " + ($block * 4) + "  " + ($block * 2))
  Write-Host ("  " + ($block * 2) + "    " + ($block * 2))
  Write-Host ""
}

function Test-InCells {
  param([int]$Y, [int]$X, [string]$Cells)

  foreach ($item in ($Cells -split " ")) {
    if ($item -eq "$Y,$X") {
      return $true
    }
  }
  return $false
}

function Test-InPiece {
  param([int]$Y, [int]$X, [int]$PieceY, [int]$PieceX, [string]$Cells)

  foreach ($item in ($Cells -split " ")) {
    $parts = $item -split ","
    if (($Y -eq ($PieceY + [int]$parts[0])) -and ($X -eq ($PieceX + [int]$parts[1]))) {
      return $true
    }
  }
  return $false
}

function Get-LogoCellColor {
  param(
    [int]$Phase,
    [string]$Active,
    [int]$ActiveX,
    [int]$ActiveY,
    [int]$Flash,
    [int]$White,
    [int]$Y,
    [int]$X
  )

  if ($White -eq 1) {
    if (Test-InCells $Y $X "3,2 3,3 3,4 4,2 4,4 5,2 5,3 5,5 6,2 6,5") { return "white" }
    return "panel"
  }
  if (($Flash -eq 1) -and ($Y -eq 6) -and ($X -ge 1) -and ($X -le 6)) { return "flash" }

  if (($Active -eq "left") -and (Test-InPiece $Y $X $ActiveY $ActiveX "0,0 1,0 1,1 2,0")) { return "red" }
  if (($Active -eq "top") -and (Test-InPiece $Y $X $ActiveY $ActiveX "0,0 0,1 0,2 1,2")) { return "cyan" }
  if (($Active -eq "right") -and (Test-InPiece $Y $X $ActiveY $ActiveX "0,0 1,0 2,0 2,1")) { return "green" }

  if ($Phase -eq 4) {
    if (Test-InCells $Y $X "2,2 2,3 2,4 3,4") { return "cyan" }
    if (Test-InCells $Y $X "3,2 4,2 4,3 5,2") { return "red" }
    if (Test-InCells $Y $X "4,5 5,5") { return "green" }
    return "panel"
  }

  if ($Phase -ge 5) {
    if (Test-InCells $Y $X "3,2 3,3 3,4 4,4") { return "cyan" }
    if (Test-InCells $Y $X "4,2 5,2 5,3 6,2") { return "red" }
    if (Test-InCells $Y $X "5,5 6,5") { return "green" }
    return "panel"
  }

  if (($Phase -le 3) -and (Test-InCells $Y $X "6,1 6,2 6,3 6,4")) { return "orange" }
  if (($Phase -ge 2) -and (Test-InCells $Y $X "2,2 2,3 2,4 3,4")) { return "cyan" }
  if (($Phase -ge 1) -and (Test-InCells $Y $X "3,2 4,2 4,3 5,2")) { return "red" }
  if (($Phase -ge 3) -and (Test-InCells $Y $X "4,5 5,5 6,5 6,6")) { return "green" }

  return "panel"
}

function Write-LogoFrame {
  param(
    [string]$Clear,
    [string]$Reset,
    [int]$Phase,
    [string]$Active,
    [int]$ActiveX,
    [int]$ActiveY,
    [int]$Flash,
    [int]$White
  )

  $blockCell = ([string][char]0x2588) * 2
  $cells = @{
    panel = "$Reset  "
    cyan = "${PiEsc}[36m$blockCell"
    red = "${PiEsc}[31m$blockCell"
    green = "${PiEsc}[32m$blockCell"
    orange = "${PiEsc}[33m$blockCell"
    white = "${PiEsc}[39m$blockCell"
    flash = "${PiEsc}[33m$blockCell"
  }

  $frame = $Clear
  foreach ($y in 0..8) {
    foreach ($x in 1..8) {
      $color = Get-LogoCellColor $Phase $Active $ActiveX $ActiveY $Flash $White $y $x
      $frame += $cells[$color]
    }
    $frame += "$Reset`n"
  }
  [Console]::Write($frame)
}

function Show-PiLogoAnimation {
  if (-not (Test-InstallerAnsiOutput)) {
    Write-StaticLogo
    return
  }

  $esc = "${PiEsc}["
  $reset = "${PiEsc}[0m"
  $clear = "${esc}H"

  [Console]::Write("${esc}?25l${esc}2J${esc}H")

  foreach ($y in 0..3) { Write-LogoFrame $clear $reset 0 "left" 2 $y 0 0; Start-Sleep -Milliseconds 75 }
  foreach ($y in 0..2) { Write-LogoFrame $clear $reset 1 "top" 2 $y 0 0; Start-Sleep -Milliseconds 75 }
  foreach ($y in 0..4) { Write-LogoFrame $clear $reset 2 "right" 5 $y 0 0; Start-Sleep -Milliseconds 75 }

  Write-LogoFrame $clear $reset 3 "none" 0 0 0 0; Start-Sleep -Milliseconds 250
  Write-LogoFrame $clear $reset 3 "none" 0 0 1 0; Start-Sleep -Milliseconds 80
  Write-LogoFrame $clear $reset 3 "none" 0 0 0 0; Start-Sleep -Milliseconds 80
  Write-LogoFrame $clear $reset 3 "none" 0 0 1 0; Start-Sleep -Milliseconds 80
  Write-LogoFrame $clear $reset 4 "none" 0 0 0 0; Start-Sleep -Milliseconds 100
  Write-LogoFrame $clear $reset 5 "none" 0 0 0 0; Start-Sleep -Milliseconds 450
  Write-LogoFrame $clear $reset 5 "none" 0 0 0 1; Start-Sleep -Milliseconds 120
  Write-LogoFrame $clear $reset 5 "none" 0 0 0 0; Start-Sleep -Milliseconds 120
  Write-LogoFrame $clear $reset 5 "none" 0 0 0 1; Start-Sleep -Milliseconds 450

  [Console]::Write("$reset${esc}?25h`n")
}

function Write-OutputLines {
  param([object[]]$Lines)

  foreach ($line in $Lines) {
    Write-Host $line
  }
}

function Test-NodeVersionIsNewEnough {
  param([string]$Version)

  $normalized = $Version.TrimStart("v")
  $parsed = [version]$normalized
  return $parsed -ge $NodeMinimum
}

function Invoke-PreflightChecks {
  $status = 0

  $node = Get-Command node -ErrorAction SilentlyContinue
  if ($node) {
    $nodeVersion = (& node --version).Trim()
    if (-not (Test-NodeVersionIsNewEnough $nodeVersion)) {
      Write-Output "error: Pi requires Node.js 22.19.0 or newer. Found $nodeVersion."
      $status = 1
    }
  } else {
    Write-Output "error: Node.js 22.19.0 or newer is required to install Pi."
    $status = 1
  }

  if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    Write-Output "error: npm is required to install Pi."
    $status = 1
  }

  if ($status -ne 0) {
    Write-Output ""
  }

  $script:PiPreflightStatus = $status
}

# Read user environment values directly from the registry instead of using
# [Environment]::GetEnvironmentVariable. The DoNotExpandEnvironmentNames flag keeps
# entries such as %USERPROFILE% literal so writing PATH back does not accidentally
# expand or rewrite user-managed variables.
function Get-UserEnv {
  param([string]$Key)

  $registerKey = Get-Item -Path "HKCU:"
  $envRegisterKey = $registerKey.OpenSubKey("Environment")
  $envRegisterKey.GetValue($Key, $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
}

# Tell Explorer and newly launched terminals that HKCU:\Environment changed.
# Without this broadcast, PATH updates generally require signing out or restarting
# Windows before other processes notice them.
function Publish-EnvChange {
  if (-not ("Win32.NativeMethods" -as [Type])) {
    Add-Type -Namespace Win32 -Name NativeMethods -MemberDefinition @"
[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(
    IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam,
    uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
"@
  }

  $hwndBroadcast = [IntPtr]0xffff
  $wmSettingChange = 0x1a
  $result = [UIntPtr]::Zero
  [Win32.NativeMethods]::SendMessageTimeout($hwndBroadcast, $wmSettingChange, [UIntPtr]::Zero, "Environment", 2, 5000, [ref]$result) | Out-Null
}

# Preserve ExpandString values when an existing variable uses percent expansion.
# This mirrors how Windows stores PATH and avoids flattening values like %APPDATA%.
function Set-UserEnv {
  param([string]$Key, [string]$Value)

  $registerKey = Get-Item -Path "HKCU:"
  $envRegisterKey = $registerKey.OpenSubKey("Environment", $true)
  if ($null -eq $Value) {
    $envRegisterKey.DeleteValue($Key)
  } else {
    $registryValueKind = if ($Value.Contains("%")) {
      [Microsoft.Win32.RegistryValueKind]::ExpandString
    } elseif ($envRegisterKey.GetValue($Key)) {
      $envRegisterKey.GetValueKind($Key)
    } else {
      [Microsoft.Win32.RegistryValueKind]::String
    }
    $envRegisterKey.SetValue($Key, $Value, $registryValueKind)
  }

  Publish-EnvChange
}

function Add-UserPathEntry {
  param([string]$Directory, [switch]$Prepend)

  # Update both the persisted user PATH and this PowerShell process. The process
  # update lets the remainder of this installer immediately find newly installed
  # node/npm/pi shims without asking the user to restart first.
  $path = (Get-UserEnv -Key "Path") -split ";" | Where-Object { $_ -and ($_ -ne $Directory) }
  if ($Prepend) {
    $path = @($Directory) + $path
  } else {
    $path += $Directory
  }
  Set-UserEnv -Key "Path" -Value ($path -join ";")

  $processPath = $env:PATH -split ";" | Where-Object { $_ -and ($_ -ne $Directory) }
  if ($Prepend) {
    $env:PATH = ((@($Directory) + $processPath) -join ";")
  } else {
    $env:PATH = (($processPath + $Directory) -join ";")
  }

  Add-PathRefreshEntry $Directory
}

function Add-PathRefreshEntry {
  param([string]$Directory)

  if (-not $script:PiPathRefreshEntries) {
    $script:PiPathRefreshEntries = @()
  }
  if ($script:PiPathRefreshEntries -notcontains $Directory) {
    $script:PiPathRefreshEntries += $Directory
  }
}

function Get-InstallerParentShell {
  $currentProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $PID"
  $parentProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($currentProcess.ParentProcessId)"
  if ($parentProcess.Name -ieq "cmd.exe") {
    return "cmd"
  }
  return "powershell"
}

function Get-PathRefreshCommand {
  param([string[]]$Directories)

  $prefix = ($Directories | Where-Object { $_ } | Select-Object -Unique) -join ";"
  if (-not $prefix) {
    return ""
  }

  if ((Get-InstallerParentShell) -eq "cmd") {
    return "set `"PATH=$prefix;%PATH%`""
  }
  return "`$env:PATH = `"$prefix;`$env:PATH`""
}

function Write-PathRefreshNote {
  if (-not $script:PiPathRefreshEntries -or $script:PiPathRefreshEntries.Count -eq 0) {
    return
  }

  $command = Get-PathRefreshCommand $script:PiPathRefreshEntries
  if (-not $command) {
    return
  }

  Write-Host ""
  Write-Host "If pi is not found in the terminal that launched this installer,"
  Write-Host "restart it or update PATH there now:"
  Write-Host ""
  Write-Host "  $command"
}

function Get-WindowsArch {
  # Use the machine environment registry value rather than process environment
  # variables so ARM64 Windows running an x64 PowerShell still resolves to arm64.
  $arch = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment").PROCESSOR_ARCHITECTURE
  if ($arch -eq "AMD64") {
    return "x64"
  }
  if ($arch -eq "ARM64") {
    return "arm64"
  }

  Write-Host "Unsupported CPU architecture for automatic dependency install: $arch"
  exit 1
}

function Invoke-DownloadFile {
  param([string]$Url, [string]$OutFile)

  # Use curl.exe explicitly: plain "curl" is an alias for Invoke-WebRequest in
  # Windows PowerShell, and curl.exe is substantially faster on older systems.
  curl.exe "-#SfLo" $OutFile $Url
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "curl.exe failed; trying Invoke-RestMethod..."
    Invoke-RestMethod -Uri $Url -OutFile $OutFile
  }
}

function Assert-NodeDownloadChecksum {
  param([string]$ShasumsPath, [string]$NodeFile, [string]$ZipPath)

  $escapedNodeFile = [regex]::Escape($NodeFile)
  $selected = Get-Content $ShasumsPath | Where-Object { $_ -match "^([a-fA-F0-9]+)\s+$escapedNodeFile$" } | Select-Object -First 1
  if (-not $selected) {
    Write-Host "No checksum was found for $NodeFile."
    exit 1
  }

  $expectedHash = ([regex]::Match($selected, "^([a-fA-F0-9]+)")).Groups[1].Value.ToLowerInvariant()
  $actualHash = (Get-FileHash $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actualHash -ne $expectedHash) {
    Write-Host "Node.js download checksum verification failed."
    Write-Host "Expected: $expectedHash"
    Write-Host "Actual:   $actualHash"
    exit 1
  }
}

function Install-NodeStandalone {
  $nodeArch = Get-WindowsArch
  $nodeDistBase = "https://nodejs.org/dist/latest-v22.x"
  # Keep the auto-installed Node.js separate from the user's normal Node setup.
  # npm itself still installs Pi globally according to npm's configured prefix.
  $nodeBaseDir = Join-Path $env:LOCALAPPDATA "pi-node"
  $nodeTmpDir = Join-Path ([System.IO.Path]::GetTempPath()) "pi-node-$PID"

  Remove-Item $nodeTmpDir -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path $nodeTmpDir, $nodeBaseDir | Out-Null

  $shasumsPath = Join-Path $nodeTmpDir "SHASUMS256.txt"
  Write-Host "Resolving Node.js binary for win-$nodeArch"
  Invoke-DownloadFile "$nodeDistBase/SHASUMS256.txt" $shasumsPath

  $nodeFile = Get-Content $shasumsPath | ForEach-Object {
    if ($_ -match "\s+(node-v.+-win-$nodeArch\.zip)$") { $Matches[1] }
  } | Select-Object -First 1

  if (-not $nodeFile) {
    Write-Host "No Node.js binary is available for win-$nodeArch."
    exit 1
  }

  $zipPath = Join-Path $nodeTmpDir $nodeFile
  Write-Host "Downloading Node.js $($nodeFile -replace '\.zip$', '')"
  Invoke-DownloadFile "$nodeDistBase/$nodeFile" $zipPath
  Write-Host "Verifying Node.js download"
  Assert-NodeDownloadChecksum $shasumsPath $nodeFile $zipPath

  Write-Host "Extracting Node.js to $nodeBaseDir"
  Expand-Archive $zipPath $nodeTmpDir -Force

  $extractedDir = Join-Path $nodeTmpDir ($nodeFile -replace "\.zip$", "")
  $currentDir = Join-Path $nodeBaseDir "current"
  Remove-Item $currentDir -Recurse -Force -ErrorAction SilentlyContinue
  Move-Item $extractedDir $currentDir -Force
  Remove-Item $nodeTmpDir -Recurse -Force

  Add-UserPathEntry $currentDir -Prepend
  Write-Host "Node.js installed at $currentDir"
}

function Read-NodeNpmInstallChoice {
  if (-not (Test-InstallerInteractiveInput)) {
    Write-Host "No terminal detected; install Node.js 22.19.0 or newer and npm, then run this installer again."
    return $false
  }

  $answer = Read-Host "Pi needs Node.js 22.19.0 or newer and npm. Install standalone Node.js now? [Y/n]"
  if ($answer -match "^(n|no)$") {
    Write-Host ""
    Write-Host "Will skip Node.js install."
    return $false
  }

  return $true
}

function Get-PiAgentDir {
  return Join-Path ([Environment]::GetFolderPath("UserProfile")) ".pi\agent"
}

function Get-PiSettingsPath {
  return Join-Path (Get-PiAgentDir) "settings.json"
}

function Get-PiManagedGitBashDir {
  return Join-Path (Get-PiAgentDir) "win-git-bash"
}

function Get-PiManagedGitBashPath {
  return Join-Path (Join-Path (Get-PiManagedGitBashDir) "bin") "bash.exe"
}

function Get-PiSettingsShellPath {
  $settingsPath = Get-PiSettingsPath
  if (-not (Test-Path $settingsPath -PathType Leaf)) {
    return ""
  }

  $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
  if ($settings -and ($settings.PSObject.Properties.Name -contains "shellPath")) {
    return [string]$settings.shellPath
  }
  return ""
}

function Set-PiSettingsShellPath {
  param([string]$ShellPath)

  $settingsPath = Get-PiSettingsPath
  New-Item -ItemType Directory -Force -Path (Split-Path $settingsPath -Parent) | Out-Null

  if (Test-Path $settingsPath -PathType Leaf) {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
  } else {
    $settings = [PSCustomObject]@{}
  }
  if ($null -eq $settings) {
    $settings = [PSCustomObject]@{}
  }

  $settings | Add-Member -MemberType NoteProperty -Name "shellPath" -Value $ShellPath -Force
  $json = $settings | ConvertTo-Json -Depth 100
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($settingsPath, "$json`r`n", $utf8NoBom)
}

function Find-BashOnPath {
  $command = Get-Command bash.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($command -and $command.Source -and (Test-Path $command.Source -PathType Leaf)) {
    return $command.Source
  }
  return ""
}

function Find-GitBashInKnownLocations {
  $paths = @()
  if ($env:ProgramFiles) {
    $paths += Join-Path (Join-Path $env:ProgramFiles "Git") "bin\bash.exe"
  }
  $programFilesX86 = ${env:ProgramFiles(x86)}
  if ($programFilesX86) {
    $paths += Join-Path (Join-Path $programFilesX86 "Git") "bin\bash.exe"
  }

  foreach ($path in $paths) {
    if (Test-Path $path -PathType Leaf) {
      return $path
    }
  }

  return Find-BashOnPath
}

function Find-ExistingBashForPi {
  $configuredShellPath = Get-PiSettingsShellPath
  if ($configuredShellPath) {
    if (Test-Path $configuredShellPath -PathType Leaf) {
      return $configuredShellPath
    }
    return ""
  }

  return Find-GitBashInKnownLocations
}

function Test-WingetAvailable {
  return [bool](Get-Command winget.exe -ErrorAction SilentlyContinue)
}

function Read-GitBashInstallChoice {
  if (-not (Test-InstallerInteractiveInput)) {
    Write-Host "No terminal detected; skipping optional Git Bash install. Install Git for Windows or set shellPath in settings.json for Pi bash commands."
    return "none"
  }

  $gitDir = Get-PiManagedGitBashDir
  $wingetAvailable = Test-WingetAvailable

  Write-Host "Pi needs Git Bash for bash commands."
  Write-Host ""
  Write-Host "Choose Git Bash install method:"
  Write-Host ""
  Write-Host "  y     Install managed Portable Git under $gitDir (default)"
  if ($wingetAvailable) {
    Write-Host "  w     Install Git for Windows globally with winget"
  }
  Write-Host "  n     Skip Git Bash"
  Write-Host ""

  while ($true) {
    $prompt = if ($wingetAvailable) { "Choice [Y/w/n]" } else { "Choice [Y/n]" }
    $answer = Read-Host $prompt
    if (-not $answer -or $answer -match "^(y|yes)$") {
      return "portable"
    }
    if ($wingetAvailable -and ($answer -match "^(w|winget)$")) {
      return "winget"
    }
    if ($answer -match "^(n|no)$") {
      Write-Host ""
      Write-Host "Will skip Git Bash install."
      return "none"
    }

    Write-Host "Please choose one of the listed keys."
  }
}

function Get-PortableGitAsset {
  $gitArch = Get-WindowsArch
  $assetSuffix = if ($gitArch -eq "arm64") { "arm64.7z.exe" } else { "64-bit.7z.exe" }

  Write-Host "Resolving Portable Git for win-$gitArch"
  $release = Invoke-RestMethod -Uri $GitForWindowsLatestReleaseApi -Headers @{ "User-Agent" = "pi-installer" }
  $asset = $release.assets | Where-Object { $_.name -like "PortableGit-*$assetSuffix" } | Select-Object -First 1
  if (-not $asset) {
    Write-Host "No Portable Git binary is available for win-$gitArch."
    exit 1
  }

  $escapedAssetName = [regex]::Escape($asset.name)
  $checksumMatch = [regex]::Match($release.body, "(?m)^$escapedAssetName\s+\|\s+([a-fA-F0-9]{64})\s*$")
  if (-not $checksumMatch.Success) {
    Write-Host "No checksum was found for $($asset.name)."
    exit 1
  }

  return [PSCustomObject]@{
    Name = $asset.name
    Url = $asset.browser_download_url
    Sha256 = $checksumMatch.Groups[1].Value.ToLowerInvariant()
  }
}

function Assert-PortableGitDownloadChecksum {
  param([string]$ExpectedHash, [string]$PortableGitPath)

  $actualHash = (Get-FileHash $PortableGitPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actualHash -ne $ExpectedHash) {
    Write-Host "Portable Git download checksum verification failed."
    Write-Host "Expected: $ExpectedHash"
    Write-Host "Actual:   $actualHash"
    exit 1
  }
}

function Install-GitBashWithWinget {
  if (-not (Test-WingetAvailable)) {
    Write-Host "winget.exe was not found."
    exit 1
  }

  Write-Host "Installing Git for Windows globally with winget"
  Write-Host ""
  Write-Host "  winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements"
  Write-Host ""

  & winget.exe install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  $installedBash = Find-GitBashInKnownLocations
  if ($installedBash) {
    $configuredShellPath = Get-PiSettingsShellPath
    if ($configuredShellPath -and (-not (Test-Path $configuredShellPath -PathType Leaf))) {
      Set-PiSettingsShellPath $installedBash
      Write-Host "Pi shellPath set to $installedBash"
    }
    Write-Host "Git Bash installed at $installedBash"
  } else {
    Write-Host "Git for Windows was installed, but Pi cannot find bash in this terminal yet."
    Write-Host "Restart your shell before using Pi bash commands."
  }
}

function Install-GitBashStandalone {
  $gitDir = Get-PiManagedGitBashDir
  $gitBashPath = Get-PiManagedGitBashPath
  if (Test-Path $gitBashPath -PathType Leaf) {
    Set-PiSettingsShellPath $gitBashPath
    Write-Host "Git Bash configured at $gitBashPath"
    return
  }

  $gitTmpDir = Join-Path ([System.IO.Path]::GetTempPath()) "pi-git-bash-$PID"
  $gitExtractDir = Join-Path $gitTmpDir "extract"

  Remove-Item $gitTmpDir -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path $gitTmpDir, $gitExtractDir, (Get-PiAgentDir) | Out-Null

  $asset = Get-PortableGitAsset
  $portableGitPath = Join-Path $gitTmpDir $asset.Name
  Write-Host "Downloading Portable Git $($asset.Name -replace '^PortableGit-', '' -replace '\.7z\.exe$', '')"
  Invoke-DownloadFile $asset.Url $portableGitPath
  Write-Host "Verifying Portable Git download"
  Assert-PortableGitDownloadChecksum $asset.Sha256 $portableGitPath

  Write-Host "Extracting Portable Git to $gitDir"
  $extractProcess = Start-Process -FilePath $portableGitPath -ArgumentList @("-y", "-o`"$gitExtractDir`"") -PassThru -Wait -WindowStyle Hidden
  if ($extractProcess.ExitCode -ne 0) {
    Write-Host "Portable Git extraction failed."
    exit $extractProcess.ExitCode
  }

  $extractedBashPath = Join-Path (Join-Path $gitExtractDir "bin") "bash.exe"
  if (-not (Test-Path $extractedBashPath -PathType Leaf)) {
    Write-Host "Portable Git extraction did not produce bin\bash.exe."
    exit 1
  }

  Remove-Item $gitDir -Recurse -Force -ErrorAction SilentlyContinue
  Move-Item $gitExtractDir $gitDir -Force
  Remove-Item $gitTmpDir -Recurse -Force

  Set-PiSettingsShellPath $gitBashPath
  Write-Host "Git Bash installed at $gitDir"
  Write-Host "Pi shellPath set to $gitBashPath"
}

function Get-NpmGlobalPrefix {
  $prefix = (& npm.cmd prefix -g 2>$null).Trim()
  if ($prefix) {
    return $prefix
  }

  return (& npm.cmd config get prefix 2>$null).Trim()
}

function Test-PathWritableOrCreatable {
  param([string]$Path)

  $checkPath = $Path
  while (-not (Test-Path $checkPath)) {
    $parent = Split-Path $checkPath -Parent
    if (-not $parent -or $parent -eq $checkPath) {
      return $false
    }
    $checkPath = $parent
  }

  if (-not (Test-Path $checkPath -PathType Container)) {
    return $false
  }

  $probe = Join-Path $checkPath ".pi-write-test-$PID"
  try {
    New-Item -ItemType File -Path $probe -Force | Out-Null
    Remove-Item $probe -Force
    return $true
  } catch [System.UnauthorizedAccessException] {
    return $false
  } catch [System.Management.Automation.ActionPreferenceStopException] {
    if ($_.Exception.InnerException -is [System.UnauthorizedAccessException]) {
      return $false
    }
    throw
  }
}

function Test-NpmPrefixSupportsGlobalInstall {
  param([string]$Prefix)

  return (Test-PathWritableOrCreatable (Join-Path $Prefix "node_modules")) -and (Test-PathWritableOrCreatable $Prefix)
}

function Get-PiBinDir {
  if ($env:PI_NPM_INSTALL_PREFIX) {
    return $env:PI_NPM_INSTALL_PREFIX
  }

  return Get-NpmGlobalPrefix
}

function Get-PiInstalledPaths {
  $binDir = Get-PiBinDir
  if ($binDir) {
    return @((Join-Path $binDir "pi.cmd"), (Join-Path $binDir "pi.ps1"))
  }

  return @()
}

function Remove-BlockedPiPowerShellShim {
  $executionPolicy = Get-ExecutionPolicy
  if ($executionPolicy -notin @("Restricted", "AllSigned")) {
    return
  }

  # npm creates both pi.cmd and pi.ps1, and PowerShell resolves the .ps1 shim
  # first. Under these policies that makes `pi` fail even though pi.cmd is
  # allowed, so remove only the blocked shim instead of weakening the user's
  # execution policy.
  $binDir = Get-PiBinDir
  $cmdShim = Join-Path $binDir "pi.cmd"
  $powerShellShim = Join-Path $binDir "pi.ps1"
  if ((Test-Path $cmdShim -PathType Leaf) -and (Test-Path $powerShellShim -PathType Leaf)) {
    Remove-Item $powerShellShim -Force
    Write-Host "  ok configured Pi for PowerShell's $executionPolicy execution policy"
  }
}

function Select-NpmInstallPrefix {
  $npmPrefix = Get-NpmGlobalPrefix
  if ($npmPrefix -and (Test-NpmPrefixSupportsGlobalInstall $npmPrefix)) {
    return ""
  }

  # If an existing global pi is present but npm's prefix is not writable, do not
  # install a second copy elsewhere: PATH would likely continue resolving to the
  # old shim, making the successful install look broken.
  $existingGlobalPi = @((Join-Path $npmPrefix "pi.cmd"), (Join-Path $npmPrefix "pi.ps1")) | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($npmPrefix -and $existingGlobalPi) {
    Write-Host "npm's global directory is not writable: $npmPrefix"
    Write-Host "Pi is already installed at: $existingGlobalPi"
    Write-Host ""
    Write-Host "Installing another copy under your profile could leave your shell using the old global pi, so this installer stopped."
    exit 1
  }

  $userPrefix = Join-Path $env:APPDATA "npm"
  New-Item -ItemType Directory -Force -Path $userPrefix | Out-Null
  return $userPrefix
}

function Select-NpmUninstallPrefix {
  param([string]$ExistingPiPath)

  # On Windows npm creates command shims directly in the prefix directory
  # (pi.cmd / pi.ps1), unlike Unix where shims live under prefix/bin.
  if (-not $ExistingPiPath) {
    return ""
  }

  $npmPrefix = Get-NpmGlobalPrefix
  if ($npmPrefix -and (($ExistingPiPath -eq (Join-Path $npmPrefix "pi.cmd")) -or ($ExistingPiPath -eq (Join-Path $npmPrefix "pi.ps1")))) {
    return ""
  }

  if ($env:PI_NPM_INSTALL_PREFIX -and (($ExistingPiPath -eq (Join-Path $env:PI_NPM_INSTALL_PREFIX "pi.cmd")) -or ($ExistingPiPath -eq (Join-Path $env:PI_NPM_INSTALL_PREFIX "pi.ps1")))) {
    return $env:PI_NPM_INSTALL_PREFIX
  }

  $fileName = Split-Path $ExistingPiPath -Leaf
  if ($fileName -in @("pi.cmd", "pi.ps1", "pi")) {
    return (Split-Path $ExistingPiPath -Parent)
  }

  return ""
}

function Write-NpmInstallCommand {
  if ($env:PI_NPM_INSTALL_PREFIX) {
    Write-Output "npm.cmd install -g --ignore-scripts $NpmMinReleaseAgeArg --prefix `"$env:PI_NPM_INSTALL_PREFIX`" $PiPackage"
  } else {
    Write-Output "npm.cmd install -g --ignore-scripts $NpmMinReleaseAgeArg $PiPackage"
  }
}

function Write-PiActionMenu {
  param([string]$ExistingPiPath)

  $reset = ""
  $dim = ""
  $bold = ""
  $cyan = ""
  $green = ""
  $red = ""
  if (Test-InstallerAnsiOutput) {
    $reset = "${PiEsc}[0m"
    $dim = "${PiEsc}[2m"
    $bold = "${PiEsc}[1m"
    $cyan = "${PiEsc}[36m"
    $green = "${PiEsc}[32m"
    $red = "${PiEsc}[31m"
  }

  if ($ExistingPiPath) {
    Write-Host "${bold}Pi is already installed at:${reset}"
    Write-Host ""
    Write-Host "  $ExistingPiPath"
    Write-Host ""
  }

  if ($env:PI_NPM_INSTALL_PREFIX) {
    Write-Host "npm's global directory is not writable; Pi will be installed under $env:PI_NPM_INSTALL_PREFIX."
    Write-Host ""
  }

  if ($ExistingPiPath) {
    Write-Host "${bold}Reinstall command:${reset}"
  } else {
    Write-Host "${bold}Install command:${reset}"
  }
  Write-Host ""
  Write-Host "  $(Write-NpmInstallCommand)"
  Write-Host ""

  Write-Host "${bold}Choose an action:${reset}"
  Write-Host ""
  if ($ExistingPiPath) {
    Write-Host ("  {0}{1,-4}{2} {3}Reinstall Pi{2} {4}(default){2}" -f $cyan, "y", $reset, $green, $dim)
    Write-Host ("  {0}{1,-4}{2} {3}Uninstall Pi{2}" -f $cyan, "u", $reset, $red)
  } else {
    Write-Host ("  {0}{1,-4}{2} {3}Install Pi{2} {4}(default){2}" -f $cyan, "y", $reset, $green, $dim)
  }
  Write-Host ("  {0}{1,-4}{2} {3}Do nothing{2}" -f $cyan, "n", $reset, $dim)
}

function Read-PiActionKey {
  $keyInfo = [Console]::ReadKey($true)
  if ($keyInfo.Key -eq [ConsoleKey]::Enter) {
    return ""
  }
  if ($keyInfo.Key -eq [ConsoleKey]::Spacebar) {
    return " "
  }
  if ($keyInfo.Key -eq [ConsoleKey]::Escape) {
    return $PiEsc
  }
  return [string]$keyInfo.KeyChar
}

function Get-DefaultPiAction {
  param([string]$ExistingPiPath)

  if ($ExistingPiPath) {
    return "reinstall"
  }
  return "install"
}

function Write-PiActionSelection {
  param([string]$Action)

  switch ($Action) {
    "install" { $message = "Will install Pi." }
    "reinstall" { $message = "Will reinstall Pi." }
    "uninstall" { $message = "Will uninstall Pi." }
    "none" { $message = "Chose to do nothing. Exiting." }
  }
  Write-Host ""
  Write-Host $message
  if ($Action -in @("install", "reinstall")) {
    Write-Host "This will take a while. We're sorry."
  }
  Write-Host ""
}

function Choose-PiAction {
  param([string]$ExistingPiPath)

  Write-PiActionMenu $ExistingPiPath
  Write-Host ""

  if (-not (Test-InstallerInteractiveInput)) {
    Write-Host "No terminal detected; continuing without confirmation."
    $action = Get-DefaultPiAction $ExistingPiPath
    Write-PiActionSelection $action
    return $action
  }

  while ($true) {
    $key = Read-PiActionKey

    if (($key -eq "") -or ($key -eq " ")) {
      $action = Get-DefaultPiAction $ExistingPiPath
      break
    }
    if ($key -match "^(y|Y)$") {
      $action = Get-DefaultPiAction $ExistingPiPath
      break
    }
    if ($ExistingPiPath -and ($key -match "^(u|U)$")) {
      $action = "uninstall"
      break
    }
    if (($key -match "^(n|N)$") -or ($key -eq $PiEsc)) {
      $action = "none"
      break
    }

    Write-Host "Please choose one of the listed keys."
  }

  Write-PiActionSelection $action
  return $action
}

function Get-NpmInstallPiArgs {
  param([string]$LogLevel, [string]$Progress)

  $args = @("install", "-g", "--ignore-scripts", $NpmMinReleaseAgeArg, "--no-fund", "--no-audit", "--loglevel=$LogLevel", "--progress=$Progress")
  if ($env:PI_NPM_INSTALL_PREFIX) {
    $args += @("--prefix", $env:PI_NPM_INSTALL_PREFIX)
  }
  $args += $PiPackage
  return $args
}

function Invoke-NpmInstallPi {
  $args = Get-NpmInstallPiArgs "error" "false"
  & npm.cmd @args
}

function Install-PiPackageWithProgress {
  $logFile = Join-Path ([System.IO.Path]::GetTempPath()) "pi-installer-npm-$PID.log"
  Remove-Item $logFile -Force -ErrorAction SilentlyContinue
  New-Item -ItemType File -Path $logFile -Force | Out-Null

  $npmArgs = [System.Collections.ArrayList]::new()
  $npmArgs.AddRange([string[]](Get-NpmInstallPiArgs "verbose" "false"))
  $job = Start-Job -ScriptBlock {
    param([string[]]$ArgsForNpm, [string]$OutputLog)

    & npm.cmd @ArgsForNpm *> $OutputLog
    $LASTEXITCODE
  } -ArgumentList $npmArgs, $logFile

  [Console]::Write("${PiEsc}[?25l")
  $script:PiLastProgressWidth = 0
  $step = 0
  $label = "starting npm install"
  $lastFrame = $null
  $lastLabel = $null
  $redrawIntervalMs = 180
  while ($job.State -eq "Running") {
    $frame = Get-SpinnerFrame $step
    if (($step % 3) -eq 0) {
      $label = Get-NpmInstallProgressLabel $logFile $label
    }
    if (($frame -ne $lastFrame) -or ($label -ne $lastLabel)) {
      Write-InstallProgress $step $frame $label "Installing Pi"
      $lastFrame = $frame
      $lastLabel = $label
    }
    $step += 1
    Start-Sleep -Milliseconds $redrawIntervalMs
  }

  $status = Receive-Job $job | Select-Object -Last 1
  Remove-Job $job
  Finish-InstallProgress

  if ($status -ne 0) {
    [Console]::Write("${PiEsc}[31mInstallation failed.${PiEsc}[0m`n`n")
    Get-Content $logFile | ForEach-Object { Write-Host $_ }
    Remove-Item $logFile -Force -ErrorAction SilentlyContinue
    exit $status
  }

  Remove-Item $logFile -Force -ErrorAction SilentlyContinue
  Write-Host "  ok npm install complete"
}

function Invoke-NpmUninstallPi {
  $args = @("uninstall", "-g", "--no-fund", "--no-audit", "--loglevel=error", "--progress=false")
  if ($env:PI_NPM_UNINSTALL_PREFIX) {
    $args += @("--prefix", $env:PI_NPM_UNINSTALL_PREFIX)
  }
  $args += $PiPackage
  & npm.cmd @args
}

function Test-NpmPackageInstalledForUninstall {
  $args = @("ls", "-g", "--depth=0")
  if ($env:PI_NPM_UNINSTALL_PREFIX) {
    $args += @("--prefix", $env:PI_NPM_UNINSTALL_PREFIX)
  }
  $args += $PiPackage
  & npm.cmd @args *> $null
  return $LASTEXITCODE -eq 0
}

function Install-PiPackage {
  if (Test-InstallerAnsiOutput) {
    Install-PiPackageWithProgress
  } else {
    Write-Host "Installing Pi..."
    Write-Host ""
    Invoke-NpmInstallPi
    if ($LASTEXITCODE -ne 0) {
      exit $LASTEXITCODE
    }
  }
}

function Uninstall-PiPackage {
  if (-not (Test-NpmPackageInstalledForUninstall)) {
    Write-Host "I found pi at:"
    Write-Host ""
    Write-Host "  $env:PI_EXISTING_PATH"
    Write-Host ""
    Write-Host "but npm does not show $PiPackage installed there."
    Write-Host "Nothing was removed."
    exit 1
  }

  Write-Host "Uninstalling Pi..."
  Write-Host ""
  Invoke-NpmUninstallPi
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  if ((Test-Path $env:PI_EXISTING_PATH) -or (Test-Path $env:PI_EXISTING_PATH -PathType Leaf)) {
    Write-Host ""
    Write-Host "npm uninstall finished, but pi is still present at:"
    Write-Host ""
    Write-Host "  $env:PI_EXISTING_PATH"
    exit 1
  }
}

function Test-InstalledPiIsFirstOnPath {
  $installedPiPaths = Get-PiInstalledPaths
  if (-not $installedPiPaths) {
    return $false
  }

  $activePi = Get-Command $PiCmd -ErrorAction SilentlyContinue
  return $activePi -and ($installedPiPaths -contains $activePi.Source)
}

function Write-PiNotOnPathMessage {
  $piBinDir = Get-PiBinDir
  $activePi = Get-Command $PiCmd -ErrorAction SilentlyContinue

  Write-Host "Pi was installed, but your shell is not using that install yet."
  if ($activePi) {
    Write-Host "Your shell currently resolves pi to: $($activePi.Source)"
  }

  if ($piBinDir) {
    $answer = Read-Host "Add $piBinDir to your user PATH now? [Y/n]"
    if (-not $answer -or $answer -notmatch "^(n|no)$") {
      Add-UserPathEntry $piBinDir -Prepend
      Write-Host "Added $piBinDir to your user PATH."
    }
    Write-Host "Restart your shell, then run: pi"
  } else {
    Write-Host "Check npm's global prefix with: npm prefix -g"
    Write-Host "Then add that directory to your PATH."
  }
}

function Invoke-PiInstaller {
  if ([System.Environment]::OSVersion.Platform -ne "Win32NT") {
    Write-Host "This PowerShell installer is for Windows. On Unix, use: curl -fsSL https://pi.dev/install.sh | sh"
    exit 1
  }

  $preflightOutput = Invoke-PreflightChecks
  $preflightStatus = $script:PiPreflightStatus

  Show-PiLogoAnimation
  Write-InstallerTitle
  if ($script:PiPreflightStatus -eq 0) {
    Write-OutputLines $preflightOutput
  }

  $installNode = $false
  if ($script:PiPreflightStatus -ne 0) {
    $installNode = Read-NodeNpmInstallChoice
  }

  if ($installNode) {
    Write-Host ""
    Install-NodeStandalone
    Write-Host ""
  }

  if ($preflightStatus -ne 0) {
    $preflightOutput = Invoke-PreflightChecks
    Write-OutputLines $preflightOutput
    if ($script:PiPreflightStatus -ne 0) {
      exit $script:PiPreflightStatus
    }
  }

  $existingPi = Get-Command $PiCmd -ErrorAction SilentlyContinue
  if ($existingPi) {
    $env:PI_EXISTING_PATH = $existingPi.Source
  } else {
    $env:PI_EXISTING_PATH = ""
  }

  $installPrefix = Select-NpmInstallPrefix
  if ($installPrefix) {
    $env:PI_NPM_INSTALL_PREFIX = $installPrefix
  } else {
    $env:PI_NPM_INSTALL_PREFIX = ""
  }

  $uninstallPrefix = Select-NpmUninstallPrefix $env:PI_EXISTING_PATH
  if ($uninstallPrefix) {
    $env:PI_NPM_UNINSTALL_PREFIX = $uninstallPrefix
  } else {
    $env:PI_NPM_UNINSTALL_PREFIX = ""
  }

  $action = Choose-PiAction $env:PI_EXISTING_PATH
  if ($action -eq "uninstall") {
    Uninstall-PiPackage
    Write-Host ""
    Write-Host "Pi was uninstalled successfully."
    exit 0
  }
  if ($action -eq "none") {
    exit 0
  }

  $existingBash = Find-ExistingBashForPi
  if (-not $existingBash) {
    $gitBashInstallMethod = Read-GitBashInstallChoice
    if ($gitBashInstallMethod -eq "portable") {
      Write-Host ""
      Install-GitBashStandalone
      Write-Host ""
    } elseif ($gitBashInstallMethod -eq "winget") {
      Write-Host ""
      Install-GitBashWithWinget
      Write-Host ""
    }
  }

  Install-PiPackage
  Remove-BlockedPiPowerShellShim
  Write-Host ""
  if ($action -eq "reinstall") {
    Write-Host "Pi was reinstalled successfully."
  } else {
    Write-Host "Pi was installed successfully."
  }

  if (Test-InstalledPiIsFirstOnPath) {
    Write-Host ""
    Write-Host "Run it with: pi"
  } else {
    Write-Host ""
    Write-PiNotOnPathMessage
  }

  Write-PathRefreshNote
}

Invoke-PiInstaller
