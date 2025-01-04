from pyee.base import EventEmitter
from pyee.asyncio import AsyncIOEventEmitter
from enum import Enum


class UserActionEvent(Enum):
    """
    Declare application events
    """

    MO_NO_CHANGE = "mo_no_change"
    MO_NOSEQ_CHANGE = "mo_noseq_change"
    SIZE_LIST_CHANGE = "size_list_change"
    SELECTED_SIZE_CHANGE = "selected_size_change"
    EPC_DATA_CHANGE = ("epc_data_change",)
    COMBINED_EPC_CREATED = "combined_epc_created"


sync_event_emitter = EventEmitter()

async_event_emitter = AsyncIOEventEmitter()
