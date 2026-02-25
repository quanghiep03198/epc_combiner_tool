from os import path
from dotenv import dotenv_values, set_key
from constants import DB_DRIVER, DB_PORT
from configparser import ConfigParser
from helpers.logger import logger
from enum import Enum
from typing import Any, Callable

__cfg_file__ = path.abspath(
    path.join(path.dirname(path.abspath(__file__)), "../app.cfg")
)
"""
Create default app.cfg file if it doesn't exist
"""
if not path.exists(__cfg_file__):
    config = ConfigParser()
    config.add_section("LOCALE")
    config.set("LOCALE", "language", "en")
    config.add_section("DATA")
    config.set("DATA", "auto_save", "True")
    config.add_section("UI")
    config.set("UI", "theme", "dark")

    with open(__cfg_file__, "w", encoding="utf-8") as file:
        config.write(file)

__configs__ = ConfigParser()
__configs__.read(filenames=__cfg_file__)

# Ensure required sections exist in the config file (and create with sensible defaults if missing)
_required_sections = {
    "LOCALE": {"language": "en"},
    "DATA": {"auto_save": "True"},
    "UI": {"theme": "dark"},
}

_changed = False
for _section, _defaults in _required_sections.items():
    if not __configs__.has_section(_section):
        __configs__.add_section(_section)
        for _k, _v in _defaults.items():
            __configs__.set(_section, _k, str(_v))
        _changed = True

if _changed:
    with open(__cfg_file__, "w", encoding="utf-8") as _file:
        __configs__.write(_file)


class ConfigSection(Enum):
    LOCALE = "LOCALE"
    DATA = "DATA"
    UI = "UI"


class ConfigService:

    @staticmethod
    def load_configs() -> dict[str, str | None]:
        """
        Load configurations from .env file
        """
        if not path.exists(".env"):
            with open(".env", "w") as configfile:
                configfile.write(f"DB_DRIVER='{DB_DRIVER}'\n")
                configfile.write("DB_SERVER=\n")
                configfile.write(f"DB_PORT='{DB_PORT}'\n")
                configfile.write("DB_UID=\n")
                configfile.write("DB_PWD=\n\n")
                configfile.write("UHF_READER_TCP_IP=\n")
                configfile.write("UHF_READER_TCP_PORT=\n")
                configfile.write("UHF_READER_POWER='20'")

        return dotenv_values(".env")

    @staticmethod
    def get_env(
        key: str,
        serializer: Callable[[str], Any] | None = None,
    ) -> str:
        configs = ConfigService.load_configs()
        value = configs.get(key)
        if serializer and callable(serializer):
            return serializer(value)
        return value

    @staticmethod
    def set_env(key: str, value: str):
        set_key(".env", key, value)

    @staticmethod
    def get_conf(
        section: str,
        key: str,
        default: Any = None,
        serializer: Callable[[str], Any] | None = None,
    ) -> str:
        if __configs__.has_option(section, key):
            value = __configs__.get(section, key, fallback=default)
            if serializer and callable(serializer):
                return serializer(value)
            return value

        logger.warning(f"Config key {key} not found in section {section}")
        return default

    @staticmethod
    def set_conf(section: ConfigSection, key: str, value: Any) -> None:
        # if not __configs__.has_section(section):
        #     __configs__.add_section(section)
        __configs__.set(section, key, str(value))
        with open(file=__cfg_file__, mode="w", encoding="utf-8") as file:
            __configs__.write(file)
