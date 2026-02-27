from enum import Enum


class RequestType(str, Enum):
    SINGLE = "single"
    COMPOSED = "composed"


class RequestStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    QUOTED = "quoted"
    BOOKED = "booked"
    CANCELLED = "cancelled"


class OptimizationMode(str, Enum):
    FASTEST = "fastest"
    CHEAPEST = "cheapest"
    BALANCED = "balanced"
