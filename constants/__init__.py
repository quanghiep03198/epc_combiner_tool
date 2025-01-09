from enum import Enum, unique

global DB_DRIVER
global DB_SERVER_DEFAULT

DB_DRIVER = "SQL Server"
DB_SERVER_DEFAULT = "10.30.0.21"


@unique
class CombineAction(Enum):
    COMBINE_NEW = "A"
    COMPENSATE = "D"


@unique
class CombineType(Enum):
    BY_MO_NO = 0
    BY_MO_NOSEQ = 1


@unique
class FactoryNames(Enum):
    VA1 = "Liên Dinh"
    VB2 = "Liên Thuấn 2"
    CA1 = "Cambodia"


@unique
class StatusCode(Enum):
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
