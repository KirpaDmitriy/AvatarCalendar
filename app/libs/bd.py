from typing import  Any, Dict, Optional, List
from datetime import datetime

event_collection = None # таблица базы данных с событями

from models.event import EventCalendar

SearchCondition = Dict[str, Any]

async def get_time_segment_user_events(
    user_id,
    event_beginning: bool,
    before_ts: Optional[datetime] = None,
    after_ts: Optional[datetime] = None,
    sort_required: bool = False,
):  # достаёт события пользователя, входящие в промежуток между before_ts и after_ts
    event_coll = event_collection()
    checked_time_field = "date_time_begin"
    if not event_beginning:
        checked_time_field = "date_time_end"
    time_filter = {}
    if not before_ts and after_ts:
        time_filter[checked_time_field] = {"$gte": after_ts}
    if not after_ts and before_ts:
        time_filter[checked_time_field] = {"$lte": before_ts}
    if after_ts and before_ts:
        time_filter["$and"] = [
            {checked_time_field: {"$lte": before_ts}},
            {checked_time_field: {"$gte": after_ts}}
        ]

    query = {}
    query: Dict[str, List[SearchCondition]] = {
        "$and": [
            time_filter,
            {
                "$or": [
                    {"owner_id": user_id},
                    {"curator_id": user_id},
                    {"members": user_id},
                ]
            }
        ]
    }
    cursor = None
    if sort_required:
        cursor = event_coll.find(query).sort("date_time_begin", 1)
    else:
        cursor = event_coll.find(query)
    return cursor


async def check_intersections(
    event: EventCalendar,
    user_id
) -> List[EventCalendar]:  # список событий, накладывающихся на переданное в аргументах событие

    overlapping_events_cursor_bin = await get_time_segment_user_events(
        user_id=user_id,
        before_ts=event.date_time_end,
        after_ts=event.date_time_begin,
        event_beginning=True
    )
    intersecting_events = [EventCalendar(**event) async for event in overlapping_events_cursor_bin]
    
    overlapping_events_cursor_fin = await get_time_segment_user_events(
        user_id=user_id,
        before_ts=event.date_time_end,
        after_ts=event.date_time_begin,
        event_beginning=False
    )
    intersecting_events.extend([EventCalendar(**event) async for event in overlapping_events_cursor_fin])
    
    enveloping_events_cursor = await get_enveloping_user_events(
        user_id=user_id,
        begin_ts=event.date_time_begin,
        end_ts=event.date_time_end
    )
    intersecting_events.extend([EventCalendar(**event) async for event in enveloping_events_cursor])

    return intersecting_events


async def get_enveloping_user_events(
    user_id,
    begin_ts: Optional[datetime] = None,
    end_ts: Optional[datetime] = None,
):  # вспом функция, которая доставала события, целиком включающие переданное в аргументах. Пример: пары с 9 до 18, обед с 13 до 14. Для события обед вернёт событие пары
    event_coll = event_collection()
    time_filter = {}
    if not begin_ts and end_ts:
        begin_ts = end_ts
    if not end_ts and begin_ts:
        end_ts = begin_ts
    time_filter["$and"] = [
        {"date_time_end": {"$gte": end_ts}},
        {"date_time_begin": {"$lte": begin_ts}}
    ]

    query = {}
    query: Dict[str, List[SearchCondition]] = {
        "$and": [
            time_filter,
            {
                "$or": [
                    {"owner_id": user_id},
                    {"curator_id": user_id},
                    {"members": user_id},
                ]
            }
        ]
    }
    cursor = event_coll.find(query)
    return cursor
