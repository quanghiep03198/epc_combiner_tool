import sys
from PyQt6.QtWidgets import *
from PyQt6.QtSql import QSqlDatabase
from helpers.logger import logger
from enum import Enum
from helpers.configuration import ConfigService
from dotenv import load_dotenv
from constants import DB_DRIVER

load_dotenv()

global DATA_SOURCE_ERP
global DATA_SOURCE_DL
global DATA_SOURCE_SYSCLOUD


class DataSources(Enum):
    DATA_LAKE = "DV_DATA_LAKE"
    ERP = "wuerp_vnrd"
    SYSCLOUD = "syscloud_vn"


class DatabaseConnection(Enum):
    DATA_LAKE = "DATA_LAKE"
    ERP = "ERP"
    SYSCLOUD = "SYSCLOUD"


configuration = ConfigService.load_configs()


def connnect_database(server: str, database: str, connection_name: str):
    """
    Connect to database using QODBC driver
        - SQL Server is used as default database driver
        - Database connection is only established if all configurations are provided

    Args:
        - server (str): Database IP host
        - database (str): Database name
    """

    if not all(value == "" for value in configuration.values()):
        try:
            database_name = (
                f"DRIVER={DB_DRIVER};"
                f"SERVER={server};"
                f"PORT={configuration.get("DB_PORT")};"
                f"DATABASE={database};"
                f"UID={configuration.get("DB_UID")};"
                f"PWD={configuration.get("DB_PWD")};"
            )

            if QSqlDatabase.contains(connection_name):
                QSqlDatabase.removeDatabase(connection_name)

            data_source = QSqlDatabase.addDatabase("QODBC", connection_name)
            data_source.setDatabaseName(database_name)

            if not data_source.isOpen():
                data_source.open()

                if not data_source.open():
                    error = data_source.lastError().text()
                    logger.error(f"Failed to connect: {error}")
                    return None

            logger.info(f"Connected to database: {database}")
            return data_source
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None
    else:
        return None


def get_raw_sql(file_path):
    try:
        with open(file_path, "r", -1, "utf-8") as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading SQL file: {e}")
        return None


# * Setup database connection
app = QApplication(sys.argv)

QSqlDatabase.removeDatabase(QSqlDatabase.database().connectionName())

DATA_SOURCE_ERP = connnect_database(
    server=configuration.get("DB_SERVER"),
    database=DataSources.ERP.value,
    connection_name=DatabaseConnection.ERP.value,
)
DATA_SOURCE_DL = connnect_database(
    server=configuration.get("DB_SERVER"),
    database=DataSources.DATA_LAKE.value,
    connection_name=DatabaseConnection.DATA_LAKE.value,
)
DATA_SOURCE_SYSCLOUD = connnect_database(
    server=configuration.get("DB_SERVER_DEFAULT"),
    database=DataSources.SYSCLOUD.value,
    connection_name=DatabaseConnection.SYSCLOUD.value,
)
# It always connect to 21 for all database
