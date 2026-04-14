"""Configuratiepersistentie voor D-Sheet Dashboard."""

from __future__ import annotations
import json
from pathlib import Path

from app.settings import RenderSettings, ViewportSettings, AppSettings

CONFIG_DIR = Path.home() / '.dsheet_dashboard'
CONFIG_FILE = CONFIG_DIR / 'config.json'


class ConfigManager:
    """Beheert het lezen en schrijven van de gebruikersconfiguratie."""

    def __init__(self, config_file: Path | None = None) -> None:
        self._config_file = config_file or CONFIG_FILE
        self._config_dir = self._config_file.parent

    def load(self) -> tuple[RenderSettings, ViewportSettings, AppSettings]:
        """Lees config.json; geef defaults terug bij ontbreken of fouten."""
        if not self._config_file.exists():
            return RenderSettings(), ViewportSettings(), AppSettings()
        try:
            with open(self._config_file, encoding='utf-8') as f:
                cfg = json.load(f)
            rs_data = cfg.get('render_settings', {})
            vp_data = cfg.get('viewport_settings', {})
            app_data = cfg.get('app_settings', {})
            rs = RenderSettings(**{
                k: v for k, v in rs_data.items()
                if k in RenderSettings.__dataclass_fields__
            }) if rs_data else RenderSettings()
            vp = ViewportSettings(**{
                k: v for k, v in vp_data.items()
                if k in ViewportSettings.__dataclass_fields__
            }) if vp_data else ViewportSettings()
            app = AppSettings(**{
                k: v for k, v in app_data.items()
                if k in AppSettings.__dataclass_fields__
            }) if app_data else AppSettings()
            return rs, vp, app
        except Exception as exc:
            import warnings
            warnings.warn(f'Kon config.json niet lezen: {exc}', stacklevel=2)
            return RenderSettings(), ViewportSettings(), AppSettings()

    def save(self, rs: RenderSettings, vp: ViewportSettings,
             app: AppSettings) -> None:
        """Sla render-, viewport- en app-instellingen op naar config.json."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        cfg = {
            'render_settings': {f: getattr(rs, f) for f in rs.__dataclass_fields__},
            'viewport_settings': {f: getattr(vp, f) for f in vp.__dataclass_fields__},
            'app_settings': {f: getattr(app, f) for f in app.__dataclass_fields__},
        }
        with open(self._config_file, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
