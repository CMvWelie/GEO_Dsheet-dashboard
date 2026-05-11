# SETUP

Eenmalige installatiescripts voor D-Sheet Dashboard op een Windows-werkstation.
Uitvoeren na eerste installatie of na verplaatsing van de app naar een andere map.

## Bestanden

| Bestand | Doel |
|---|---|
| `maak_snelkoppeling.py` | Maakt een bureaubladsnelkoppeling aan met het juiste app-icoon. |
| `register_shd.ps1` | Koppelt `.shd`-bestanden in de Verkenner aan D-Sheet Dashboard (schrijft naar `HKCU`). |
| `register_shd.bat` | Roept `register_shd.ps1` aan met `ExecutionPolicy Bypass` — dubbelklikken volstaat. |

## Gebruik

### Bureaubladsnelkoppeling aanmaken

```bash
python SETUP/maak_snelkoppeling.py
```

Genereert `themes/Dsheet_dashboard.ico` uit de PNG en plaatst `D-Sheet Dashboard.lnk` op het bureaublad. Vereist dat `themes/Dsheet_dashboard.png` aanwezig is.

### .shd-bestandsassociatie registreren

Dubbelklik op `register_shd.bat`, of voer het PowerShell-script rechtstreeks uit:

```powershell
powershell -ExecutionPolicy Bypass -File SETUP\register_shd.ps1
```

Registreert `.shd` → `DSheetDashboard.shd` in `HKCU\Software\Classes` zodat dubbelklikken op een `.shd`-bestand de app opent. Vereist geen beheerdersrechten. Na verplaatsing van de app naar een andere map opnieuw uitvoeren.
