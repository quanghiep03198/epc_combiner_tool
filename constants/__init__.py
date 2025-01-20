from enum import Enum, unique

global DB_DRIVER, DB_SERVER_DEFAULT, DB_PORT

DB_DRIVER = "SQL Server"
DB_SERVER_DEFAULT = "10.30.0.21"
DB_PORT = 1433


@unique
class CombineAction(Enum):
    COMBINE_NEW = "A"
    COMPENSATE = "D"


@unique
class NgAction(Enum):
    COMPENSATE = 1
    CANCEL = 2


@unique
class FactoryNames(Enum):
    VA1 = "Lian Ying"
    VB1 = "Lian Shun 1"
    VB2 = "Lian Shun 2"
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
