from os import path
from dotenv import dotenv_values, set_key
from constants import DB_DRIVER, DB_SERVER_DEFAULT, DB_PORT
from configparser import ConfigParser
from helpers.logger import logger
from enum import Enum
from typing import Any, Callable

# from pathlib import Path


# __dirname = Path(__file__).parent.resolve()
__cfg_file__ = path.abspath(
    path.join(path.dirname(path.abspath(__file__)), "../app.cfg")
)
__configs__ = ConfigParser()
__configs__.read(filenames=__cfg_file__)


class ConfigSection(Enum):
    LOCALE = "LOCALE"
    DATA = "DATA"


class ConfigService:

    @staticmethod
    def load_configs() -> dict[str, str | None]:
        """
        Load configurations from .env file
        """
        if not path.exists(".env"):
            with open(".env", "w") as configfile:
                configfile.write(f"DB_DRIVER='{DB_DRIVER}'\n")
                configfile.write(f"DB_SERVER_DEFAULT='{DB_SERVER_DEFAULT}'\n")
                configfile.write("DB_SERVER=\n")
                configfile.write(f"DB_PORT='{DB_PORT}'\n")
                configfile.write("DB_UID=\n")
                configfile.write("DB_PWD=\n\n")
                configfile.write("UHF_READER_TCP_IP=\n")
                configfile.write("UHF_READER_TCP_PORT=\n")

        return dotenv_values(".env")

    @staticmethod
    def get_env(key: str) -> str:
        configs = ConfigService.load_configs()
        value = configs.get(key)
        if value:
            return value
        return None

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
            if serializer:
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
