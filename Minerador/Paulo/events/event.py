import uuid
from datetime import datetime
from typing import Any, Dict, Optional

class Event:
    def __init__(self, event_type):
        self.id = str(uuid.uuid4())
        self.type = event_type
        self.payload: Dict[str, Any] = {}
        self.timestamp = datetime.now()
        self.result: Any = None
        self.success = True
        self.error_message: Optional[str] = None

    def with_payload(self, key: str, value: Any) -> 'Event':
        self.payload[key] = value
        return self

    def get(self, key: str) -> Any:
        return self.payload.get(key)

    def get_int(self, key: str) -> Optional[int]:
        v = self.payload.get(key)
        if v is None: return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    def get_double(self, key: str) -> Optional[float]:
        v = self.payload.get(key)
        if v is None: return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    def get_string(self, key: str) -> Optional[str]:
        v = self.payload.get(key)
        return str(v) if v is not None else None

    def get_boolean(self, key: str) -> Optional[bool]:
        v = self.payload.get(key)
        if isinstance(v, bool): return v
        if isinstance(v, str): return v.lower() == 'true'
        return None

    def set_result(self, result: Any):
        self.result = result

    def set_error(self, message: str):
        self.success = False
        self.error_message = message

    def __str__(self):
        return f"Event{{id={self.id}, type={self.type}, success={self.success}}}"
