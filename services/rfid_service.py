from repositories.rfid_repository import RFIDRepository
from helpers.logger import logger
from events import sync_event_emitter, UserActionEvent
import numpy


class RFIDService:
    @staticmethod
    def reset_and_add_combinations(data: dict) -> int | None:
        """
        Cancel the previous combinations and add new the ones
        """
        try:
            epcs_to_combine = list(map(lambda item: item["EPC_Code"], data))

            # ? Check if the EPCs are not cutting new
            if not RFIDRepository.check_if_epc_new(epcs_to_combine):
                # ? If EPCs have just been combined, do not allow to combine again
                recently_combined_epcs = RFIDRepository.get_recently_combined_epcs(
                    epcs_to_combine
                )
                diff = numpy.setxor1d(epcs_to_combine, recently_combined_epcs)
                if len(list(diff)) > 0:

                    raise Exception(
                        {
                            "message": "Tồn tại tem vừa mới phối, không thể phối lại.",
                            "data": {
                                "ng_epcs": recently_combined_epcs,
                                "ok_epcs": diff,
                            },
                        }
                    )

                # ? Check if the EPCs are still in the lifecycle, if not allow user to combine them
                lifecycle_ended_epcs = RFIDRepository.get_lifecycle_ended_epcs(
                    epcs_to_combine
                )
                diff = numpy.setxor1d(epcs_to_combine, lifecycle_ended_epcs)
                if len(list(diff)) > 0:

                    raise Exception(
                        {
                            "message": "Tồn tại tem chưa sử dụng hết vòng đời, chưa thể phối lại.",
                            "data": {
                                "ng_epcs": diff,
                                "ok_epcs": lifecycle_ended_epcs,
                            },
                        }
                    )

            return RFIDRepository.reset_and_add_combinations(data)
        except Exception as e:
            raise Exception(e.args[0])

    @staticmethod
    def get_active_combinations(epcs: list[str]) -> list[dict[str, str]]:
        return RFIDRepository.get_active_combinations()
