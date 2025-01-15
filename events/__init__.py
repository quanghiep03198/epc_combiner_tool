from pyee.base import EventEmitter
from pyee.asyncio import AsyncIOEventEmitter
from enum import Enum


class UserActionEvent(Enum):
    """
    Declare application events
    """

    MO_NO_CHANGE = "mo_no_change"
    GET_ORDER_DETAIL_SUCCESS = "get_order_detail_success"
    MO_NOSEQ_CHANGE = "mo_noseq_change"
    SIZE_LIST_CHANGE = "size_list_change"
    SELECTED_SIZE_CHANGE = "selected_size_change"
    EPC_DATA_CHANGE = "epc_data_change"
    COMBINED_EPC_CREATED = "combined_epc_created"
    COMBINE_FORM_STATE_CHANGE = "combine_form_state_change"
    CHECK_COMBINABLE_FAILED = "check_combinable_failed"
    SETTINGS_CHANGE = "settings_change"
    AUTH_STATE_CHANGE = "auth_state_change"
    NG_EPC_MUTATION = "ng_epc_mutation"


global sync_event_emitter
global async_event_emitter

sync_event_emitter = EventEmitter()
async_event_emitter = AsyncIOEventEmitter()
