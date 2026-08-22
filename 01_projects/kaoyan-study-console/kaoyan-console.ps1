param(
    [ValidateSet("menu", "start", "stop", "status")]
    [string]$Action = "menu"
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendPort = 5188
$BackendPort = 8018
$FrontendUrl = "http://127.0.0.1:$FrontendPort"
$BackendUrl = "http://127.0.0.1:$BackendPort"
$System32 = Join-Path $env:SystemRoot "System32"
$CmdExe = Join-Path $System32 "cmd.exe"
$NetstatExe = Join-Path $System32 "netstat.exe"
$RuntimeDir = Join-Path $Root ".runtime"
$BackendPidFile = Join-Path $RuntimeDir "backend.pid"
$FrontendPidFile = Join-Path $RuntimeDir "frontend.pid"
$BackendLogFile = Join-Path $RuntimeDir "backend.log"
$FrontendLogFile = Join-Path $RuntimeDir "frontend.log"
$PythonExe = "python"
$NpmCmd = "npm.cmd"

function Resolve-Tool {
    param(
        [string]$CommandName,
        [string[]]$CandidatePaths
    )
    foreach ($candidate in $CandidatePaths) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }
    $found = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($found) {
        return $found.Source
    }
    return $CommandName
}

$PythonExe = Resolve-Tool -CommandName "python" -CandidatePaths @(
    "C:\Python314\python.exe",
    "C:\Python313\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Windows\py.exe"
)
$NpmCmd = Resolve-Tool -CommandName "npm.cmd" -CandidatePaths @(
    (Join-Path $env:ProgramFiles "nodejs\npm.cmd"),
    (Join-Path ${env:ProgramFiles(x86)} "nodejs\npm.cmd"),
    "$env:APPDATA\npm\npm.cmd"
)

function Ensure-RuntimeDir {
    if (-not (Test-Path $RuntimeDir)) {
        New-Item -ItemType Directory -Path $RuntimeDir | Out-Null
    }
}

function Get-PortProcessIds {
    param([int]$Port)
    if (-not (Test-Path $NetstatExe)) {
        return
    }
    $lines = & $NetstatExe -ano | Select-String -Pattern ":$Port\s+.*LISTENING"
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split "\s+") | Where-Object { $_ }
        if ($parts.Length -ge 5) {
            $parts[-1]
        }
    }
}

function Stop-Port {
    param([int]$Port)
    $pids = @(Get-PortProcessIds -Port $Port | Select-Object -Unique)
    foreach ($pidValue in $pids) {
        Write-Host "正在关闭端口 $Port，进程 PID $pidValue ..."
        Stop-Process -Id ([int]$pidValue) -Force -ErrorAction SilentlyContinue
    }
}

function Stop-PidFile {
    param([string]$PidFile)
    if (-not (Test-Path $PidFile)) {
        return
    }
    $pidText = (Get-Content -Path $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($pidText -match "^\d+$") {
        Write-Host "正在关闭已记录进程 PID $pidText ..."
        Stop-Process -Id ([int]$pidText) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
}

function Show-Port {
    param(
        [int]$Port,
        [string]$Name
    )
    $pids = @(Get-PortProcessIds -Port $Port | Select-Object -Unique)
    if ($pids.Count -eq 0) {
        Write-Host "$Name：未运行，端口 $Port 空闲"
        return
    }
    foreach ($pidValue in $pids) {
        Write-Host "$Name：正在运行，端口 $Port，进程 PID $pidValue"
    }
}

function Ensure-Dependencies {
    $nodeModules = Join-Path $Root "frontend\node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-Host "首次启动：正在安装前端依赖..."
        Push-Location (Join-Path $Root "frontend")
        & $NpmCmd install
        Pop-Location
    }
}

function Start-ManagedProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string]$Arguments,
        [string]$WorkingDirectory,
        [string]$PidFile,
        [string]$LogFile
    )
    Ensure-RuntimeDir
    if (Test-Path $LogFile) {
        Remove-Item -Path $LogFile -Force -ErrorAction SilentlyContinue
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = $Arguments
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    $process.EnableRaisingEvents = $true

    $outputAction = {
        if ($EventArgs.Data) {
            Add-Content -Path $Event.MessageData -Value $EventArgs.Data -Encoding UTF8
        }
    }

    Register-ObjectEvent -InputObject $process -EventName OutputDataReceived -Action $outputAction -MessageData $LogFile | Out-Null
    Register-ObjectEvent -InputObject $process -EventName ErrorDataReceived -Action $outputAction -MessageData $LogFile | Out-Null

    if (-not $process.Start()) {
        throw "$Name 启动失败。"
    }
    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()
    Set-Content -Path $PidFile -Value $process.Id -Encoding ASCII
    Write-Host "$Name 已启动，PID $($process.Id)。日志：$LogFile"
}

function Start-App {
    Ensure-Dependencies
    Stop-PidFile -PidFile $BackendPidFile
    Stop-PidFile -PidFile $FrontendPidFile
    Stop-Port -Port $BackendPort
    Stop-Port -Port $FrontendPort

    Write-Host ""
    Write-Host "正在启动后端：$BackendUrl"
    Start-ManagedProcess -Name "后端" -FilePath $PythonExe -Arguments "-m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort" -WorkingDirectory (Join-Path $Root "backend") -PidFile $BackendPidFile -LogFile $BackendLogFile

    Write-Host "正在启动前端：$FrontendUrl"
    if (-not (Test-Path $CmdExe)) {
        throw "找不到 cmd.exe：$CmdExe"
    }
    Start-ManagedProcess -Name "前端" -FilePath $CmdExe -Arguments "/c `"`"$NpmCmd`" run dev`"" -WorkingDirectory (Join-Path $Root "frontend") -PidFile $FrontendPidFile -LogFile $FrontendLogFile

    Write-Host "正在等待服务启动..."
    Start-Sleep -Seconds 3
    if (Test-Path $CmdExe) {
        & $CmdExe /c start "" "$FrontendUrl"
    } else {
        Start-Process $FrontendUrl
    }

    Write-Host ""
    Write-Host "已启动。浏览器地址：$FrontendUrl"
    Write-Host "使用完后回到此窗口选择 2，可以保存并关闭服务进程。"
}

function Stop-App {
    Write-Host ""
    Write-Host "正在保存并关闭..."
    Write-Host "学习数据已由网页自动保存。"
    Write-Host "如需额外备份，请下次关闭前在网页“设置”里导出 JSON。"
    Stop-PidFile -PidFile $BackendPidFile
    Stop-PidFile -PidFile $FrontendPidFile
    Stop-Port -Port $BackendPort
    Stop-Port -Port $FrontendPort
    Write-Host ""
    Write-Host "已关闭端口 $BackendPort 和 $FrontendPort 上的服务。"
}

function Wait-Enter {
    param([string]$Message = "按回车返回菜单")
    Write-Host -NoNewline $Message
    [void][Console]::ReadLine()
}

if ($Action -eq "start") {
    Start-App
    # Register-ObjectEvent 的事件接收器持有子进程管道句柄，脚本化调用（-Action start）
    # 时 powershell.exe 不会随 Start-App 返回而退出（服务本身已正常启动）。
    # 这里强制退出父进程：子进程（uvicorn / npm）独立运行，不受影响。
    # 菜单模式（默认 Action）不经过这里，行为不变。
    [Environment]::Exit(0)
    exit 0
}
if ($Action -eq "stop") {
    Stop-App
    exit 0
}
if ($Action -eq "status") {
    Show-Port -Port $BackendPort -Name "后端"
    Show-Port -Port $FrontendPort -Name "前端"
    exit 0
}

while ($true) {
    Clear-Host
    Write-Host "=========================================="
    Write-Host "          考研学习控制台"
    Write-Host "=========================================="
    Write-Host ""
    Write-Host "  1. 一键启动"
    Write-Host "  2. 保存并关闭"
    Write-Host "  3. 查看运行状态"
    Write-Host "  4. 退出此菜单"
    Write-Host ""
    Write-Host "说明："
    Write-Host "- 学习数据会自动保存在浏览器 localStorage。"
    Write-Host "- API 配置保存在 backend\llm_config.local.json。"
    Write-Host "- 需要额外备份时，请在网页“设置”里导出 JSON。"
    Write-Host ""

    Write-Host -NoNewline "请选择 1-4："
    $choice = [Console]::ReadLine()
    switch ($choice) {
        "1" { Start-App; Wait-Enter }
        "2" { Stop-App; Wait-Enter }
        "3" {
            Write-Host ""
            Show-Port -Port $BackendPort -Name "后端"
            Show-Port -Port $FrontendPort -Name "前端"
            Write-Host ""
            Wait-Enter
        }
        "4" { break }
        default { Write-Host "请输入 1、2、3 或 4。"; Start-Sleep -Seconds 1 }
    }
}
