from repositories.rfid_repository import RFIDRepository
from helpers.logger import logger
from PyQt6.QtSql import *
import numpy
from database import DATA_SOURCE_DL
from contexts.auth_context import auth_context
from events import __event_emitter__, UserActionEvent


class RFIDService:
    @staticmethod
    def reset_and_add_combinations(data: dict) -> int | None:
        """
        Cancel the previous combinations and add new the ones
        """
        try:
            return RFIDRepository.reset_and_add_combinations(data)
        except Exception as e:
            raise Exception(e.args[0])
