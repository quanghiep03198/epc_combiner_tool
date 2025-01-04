from enum import Enum


class CombineAction(Enum):
    COMBINE_NEW = 0
    COMPENSATE = 1


class CombineType(Enum):
    BY_MO_NO = 0
    BY_MO_NOSEQ = 1


