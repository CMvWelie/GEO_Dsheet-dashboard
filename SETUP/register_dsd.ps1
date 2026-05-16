# register_dsd.ps1
# Koppelt .dsd-bestanden aan D-Sheet Dashboard in de Verkenner.
# Opnieuw uitvoeren na verplaatsing van de app naar een andere map of pc.
# Vereist geen beheerdersrechten (schrijft naar HKCU).

# Herstart zichzelf met ExecutionPolicy Bypass als dat nog niet het geval is
if ($MyInvocation.MyCommand.Path -and $ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage' -or
    (Get-ExecutionPolicy -Scope Process) -eq 'Restricted') {
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Wait
    exit
}

$ErrorActionPreference = 'Stop'

$appRoot = Split-Path -Parent $PSScriptRoot
$runPyw = Join-Path $appRoot 'run.pyw'
if (-not (Test-Path $runPyw)) {
    Write-Error "run.pyw niet gevonden in $appRoot. Voer dit script uit vanuit de app-map."
    exit 1
}

# Zoek pythonw.exe — sla Windows Store-stubs over (WindowsApps zijn nep-redirectors)
$pythonw = $null
$candidates = Get-Command python -All -ErrorAction SilentlyContinue |
    Where-Object { $_.Source -notlike '*WindowsApps*' } |
    Select-Object -First 1
if ($candidates) {
    $kandidaat = Join-Path (Split-Path $candidates.Source) 'pythonw.exe'
    if (Test-Path $kandidaat) { $pythonw = $kandidaat }
}
if (-not $pythonw) {
    Write-Error "pythonw.exe niet gevonden. Controleer of Python op het PATH staat (niet als Windows Store-app)."
    exit 1
}

$progId  = 'DSheetDashboard.dsd'
$omschrijving = 'D-Sheet Dashboard sessie'
$commando = "`"$pythonw`" `"$runPyw`" `"%1`""

# .dsd -> ProgID
$null = New-Item -Path "HKCU:\Software\Classes\.dsd" -Force
Set-ItemProperty -Path "HKCU:\Software\Classes\.dsd" -Name '(default)' -Value $progId

# ProgID omschrijving
$null = New-Item -Path "HKCU:\Software\Classes\$progId" -Force
Set-ItemProperty -Path "HKCU:\Software\Classes\$progId" -Name '(default)' -Value $omschrijving

# Open-commando
$null = New-Item -Path "HKCU:\Software\Classes\$progId\shell\open\command" -Force
Set-ItemProperty -Path "HKCU:\Software\Classes\$progId\shell\open\command" -Name '(default)' -Value $commando

# Verkenner op de hoogte stellen van de wijziging
$signature = @'
[DllImport("shell32.dll")]
public static extern void SHChangeNotify(int wEventId, uint uFlags, IntPtr dwItem1, IntPtr dwItem2);
'@
Add-Type -MemberDefinition $signature -Name Shell -Namespace Win32 -ErrorAction SilentlyContinue
[Win32.Shell]::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero)

Write-Host ""
Write-Host "Klaar! .dsd-bestanden worden nu geopend met D-Sheet Dashboard."
Write-Host "  Interpreter : $pythonw"
Write-Host "  Script      : $runPyw"
Write-Host ""
Write-Host "Na verplaatsing van de app: voer dit script opnieuw uit vanuit de nieuwe map."
Write-Host ""
Read-Host "Druk op Enter om te sluiten"
