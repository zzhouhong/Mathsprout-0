import enum


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
