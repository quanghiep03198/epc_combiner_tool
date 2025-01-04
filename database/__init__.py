import sys
import asyncio
from PyQt6.QtWidgets import *
from PyQt6.QtSql import QSqlDatabase
from helpers.logger import logger  # Import logger thay vì Logger
from enum import Enum


DATABASE_DRIVER = "SQL Server"
DATABASE_HOST = "10.30.0.18"
DATABASE_PORT = 1433
DATABASE_USER = "sa"
DATABASE_PASSWORD = "greenland@VN"


class DataSources(Enum):
    DATA_LAKE = "DV_DATA_LAKE"
    ERP = "wuerp_vnrd"


def connnect_database(database: str | None):
    try:
        database_name = (
            f"DRIVER={DATABASE_DRIVER};"
            f"SERVER={DATABASE_HOST};"
            f"PORT={DATABASE_PORT};"
            f"DATABASE={database};"
            f"UID={DATABASE_USER};"
            f"PWD={DATABASE_PASSWORD}"  # Thêm thông tin đăng nhập
        )

        data_source = QSqlDatabase.addDatabase("QODBC")
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


def get_raw_sql(file_path):
    try:
        with open(file_path, "r", -1, "utf-8") as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading SQL file: {e}")
        return None


# * Setup database connection
app = QApplication(sys.argv)
# QSqlDatabase.removeDatabase(QSqlDatabase.database().connectionName())
DATA_SOURCE_ERP = connnect_database(DataSources.ERP.value)
DATA_SOURCE_DL = connnect_database(DataSources.DATA_LAKE.value)
