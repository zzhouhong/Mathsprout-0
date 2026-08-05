import enum


def enum_values_callable(enum_cls):
    """让 SQLAlchemy 原生 ENUM 使用枚举的 value（小写）作为数据库值。

    默认 SQLAlchemy 用成员名（大写，如 SMALL）建 ENUM，但业务代码里有直接写
    `.value`（小写）的路径（如 children.py 的 age_group），MySQL 原生 ENUM 会拒绝。
    SQLite（VARCHAR）两种都能存，所以这个问题只在 MySQL 上暴露。
    """
    return [m.value for m in enum_cls]


class AgeGroupEnum(str, enum.Enum):
    SMALL = "small"
    MIDDLE = "middle"
    LARGE = "large"


class UploadMethodEnum(str, enum.Enum):
    CAMERA = "camera"
    FILE = "file"
    SCAN = "scan"


class WorksheetStatusEnum(str, enum.Enum):
    UPLOADED = "uploaded"
    PREPROCESSED = "preprocessed"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ERROR = "error"


class CompletionContextEnum(str, enum.Enum):
    INDEPENDENT = "independent"
    PROMPTED = "prompted"
    ASSISTED = "assisted"


class ReportTypeEnum(str, enum.Enum):
    TEACHER = "teacher"
    PARENT = "parent"


class LevelEnum(str, enum.Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
