from app.libs.priority import PriorityEstimator
from app.libs.transfer_variants import get_cancellations
from app.models.event import EventCalendar

def get_prority(text: str):
    return PriorityEstimator.get_text_priority(text)

def get_transfer_variants(event: EventCalendar, user_id):
    return get_cancellations(event, user_id)