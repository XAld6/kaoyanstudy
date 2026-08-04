# Start Hermes gateway (0.18.2-cn.2) detached with correct HERMES_HOME.
$ErrorActionPreference = "Stop"

$rtDir = "C:\Users\Administrator\AppData\Roaming\cn.org.hermesagent.desktop\runtime"
$hermesHome = Join-Path $rtDir "hermes-home"
$exe = Join-Path $rtDir "versions\0.18.2-cn.2\hermes-agent-cn-runtime-win32-x64.exe"
$stdout = "D:\xm\90_temp_work\hermes_gateway_stdout.log"
$stderr = "D:\xm\90_temp_work\hermes_gateway_stderr.log"

if (-not (Test-Path $exe)) {
    throw "Runtime exe not found: $exe"
}

$env:HERMES_HOME = $hermesHome
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# Stop previous manual instances if any (best-effort).
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match 'hermes-agent-cn-runtime.*gateway run' } |
    ForEach-Object {
        Write-Host "Stopping old gateway PID $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Start-Sleep -Seconds 1

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $exe
$psi.Arguments = "gateway run --replace"
$psi.WorkingDirectory = $hermesHome
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.Environment["HERMES_HOME"] = $hermesHome
$psi.Environment["PYTHONUTF8"] = "1"
$psi.Environment["PYTHONIOENCODING"] = "utf-8"

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi

# Async log writers so process is not killed when this script exits.
$null = $proc.Start()
$proc.BeginOutputReadLine()
$proc.BeginErrorReadLine()
$proc.add_OutputDataReceived({
    param($sender, $e)
    if ($e.Data) { Add-Content -Path $stdout -Value $e.Data -Encoding UTF8 }
})
$proc.add_ErrorDataReceived({
    param($sender, $e)
    if ($e.Data) { Add-Content -Path $stderr -Value $e.Data -Encoding UTF8 }
})

# Prefer fully detached child via cmd start so it outlives this shell.
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

$arg = "/c start `"HermesGateway`" /B `"$exe`" gateway run --replace"
$p2 = Start-Process -FilePath "cmd.exe" -ArgumentList $arg -WorkingDirectory $hermesHome -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 8

& $exe gateway status
Write-Host "Launcher PID: $($p2.Id)"
Write-Host "Logs: $stdout / $stderr / $hermesHome\logs\agent.log"
