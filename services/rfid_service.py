from PyQt6.QtSql import *

from events import __event_emitter__
from repositories.rfid_repository import RFIDRepository


class RFIDService:
    @staticmethod
    def reset_and_add_combinations(data: list[dict]) -> int | None:
        """
        Cancel the previous combinations and add new the ones
        """
        try:
            return RFIDRepository.reset_and_add_combinations(data)
        except Exception as e:
            raise Exception(e.args[0])
