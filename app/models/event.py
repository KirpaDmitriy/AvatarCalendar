from dataclasses import dataclass
from typing import Optional
from datetime import datetime

class EventCalendar:
    title: str
    date_time_begin: Optional[datetime]
    date_time_end: Optional[datetime]
    description: Optional[str]
    location: Optional[str]
    priority: Optional[float] = 0.5