import os
from dotenv import dotenv_values, set_key
from constants import DB_DRIVER, DB_SERVER_DEFAULT


class ConfigService:

    @staticmethod
    def load_configs() -> dict[str, str | None]:

        if not os.path.exists(".env"):
            with open(".env", "w") as configfile:
                configfile.write(f"DB_DRIVER='{DB_DRIVER}'\n")
                configfile.write(f"DB_SERVER_DEFAULT='{DB_SERVER_DEFAULT}'\n")
                configfile.write("DB_SERVER=\n")
                configfile.write("DB_PORT=\n")
                configfile.write("DB_UID=\n")
                configfile.write("DB_PWD=\n\n")
                configfile.write("UHF_READER_TCP_IP=\n")
                configfile.write("UHF_READER_TCP_PORT=\n")

        return dotenv_values(".env")

    @staticmethod
    def get(key: str) -> str:
        configs = ConfigService.load_configs()
        value = configs.get(key)
        if value:
            return value
        return None

    @staticmethod
    def set(key: str, value: str):
        set_key(".env", key, value)
