# register_shd.ps1
# Koppelt .shd-bestanden aan D-Sheet Dashboard in de Verkenner.
# Opnieuw uitvoeren na verplaatsing van de app naar een andere map of pc.
# Vereist geen beheerdersrechten (schrijft naar HKCU).

$ErrorActionPreference = 'Stop'

$runPyw = Join-Path $PSScriptRoot 'run.pyw'
if (-not (Test-Path $runPyw)) {
    Write-Error "run.pyw niet gevonden in $PSScriptRoot. Voer dit script uit vanuit de app-map."
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

$progId  = 'DSheetDashboard.shd'
$omschrijving = 'D-Sheet Dashboard bestand'
$commando = "`"$pythonw`" `"$runPyw`" `"%1`""

# .shd -> ProgID
$null = New-Item -Path "HKCU:\Software\Classes\.shd" -Force
Set-ItemProperty -Path "HKCU:\Software\Classes\.shd" -Name '(default)' -Value $progId

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
Write-Host "Klaar! .shd-bestanden worden nu geopend met D-Sheet Dashboard."
Write-Host "  Interpreter : $pythonw"
Write-Host "  Script      : $runPyw"
Write-Host ""
Write-Host "Na verplaatsing van de app: voer dit script opnieuw uit vanuit de nieuwe map."
