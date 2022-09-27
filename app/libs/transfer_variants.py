from datetime import datetime, timedelta
from functools import reduce
from typing import  List

from libs.bd import get_time_segment_user_events, get_enveloping_user_events
from libs.geography import GeoStuff
from models.event import EventCalendar
from libs.priority import PriorityEstimator



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

async def generate_event_variants(user_id, duration, location_begin, location_end):
    considered_start = datetime.now().replace(minute=0, second=0) + timedelta(hours=1)
    future_events = await get_time_segment_user_events(user_id=user_id,
                                                 event_beginning=False,
                                                 after_ts=considered_start,
                                                 sort_required=True,
                                            )
    future_events = [EventCalendar(**event) async for event in future_events]
    all_time_slots = set()
    if len(future_events) == 0:
        considered_start += timedelta(hours=2)
        while not 9 <= considered_start.hour <= 18:
            considered_start += timedelta(hours=1)
        weekend_delta = 0 if considered_start.weekday() < 5 else 7 - considered_start.weekday()
        considered_start += timedelta(days=weekend_delta)
        all_time_slots.add(considered_start)
    elif len(future_events) == 1:
        only_event = future_events[0]
        considered_start = only_event.date_time_end + timedelta(days=1)
        while not 9 <= considered_start.hour <= 18:
            considered_start += timedelta(hours=1)
        weekend_delta = 0 if considered_start.weekday() < 5 else 7 - considered_start.weekday()
        considered_start += timedelta(days=weekend_delta)
        all_time_slots.add(considered_start)
    else:
        road_to_first_time = timedelta(hours=GeoStuff.calculate_time(location_end, future_events[0].location))
        if future_events[0].date_time_begin - considered_start >= duration + road_to_first_time:
            all_time_slots.add(considered_start)
        for current_event_index in range(0, len(future_events) - 1):
            current_event = future_events[current_event_index]
            next_event = future_events[current_event_index + 1]
            current_finish = current_event.date_time_end
            next_begin = next_event.date_time_begin
            road_to_time = timedelta(hours=GeoStuff.calculate_time(current_event.location, location_begin))
            road_from_time = timedelta(hours=GeoStuff.calculate_time(location_end, next_event.location))
            general_route_time = road_to_time + road_from_time
            if next_begin - current_finish >= duration + general_route_time:
                possibly_added_variant = current_finish + road_to_time

                while not 9 <= possibly_added_variant.hour <= 18:
                    possibly_added_variant += timedelta(hours=1)
                
                if possibly_added_variant.weekday() >= 5:
                    possible_weekday = possibly_added_variant.weekday()
                    change_weekday = 7 - possible_weekday
                    possibly_added_variant += timedelta(days=change_weekday)

                if next_begin >= possibly_added_variant + duration + road_from_time:
                    all_time_slots.add(possibly_added_variant)
            
            if len(all_time_slots) == 4:
                break
    
    last_event = future_events if len(future_events) > 0 else None
    last_event_end = max(last_event.date_time_end if last_event else considered_start + timedelta(hours=2), considered_start)
    location_end = last_event.location if last_event else 'online'
    road_time = timedelta(hours=GeoStuff.calculate_time(location_end, location_begin))
    latest_start = last_event_end.replace(minute=0, second=0) + timedelta(days=1) + road_time
    while not 9 <= latest_start.hour <= 18:
        latest_start += timedelta(hours=1)
    weekend_delta = 0 if latest_start.weekday() < 5 else 7 - latest_start.weekday()
    latest_start += timedelta(days=weekend_delta)
    all_time_slots.add(latest_start)
    added_days_num = 2
    
    while len(all_time_slots) < 5:
        latest_start = latest_start + timedelta(days=added_days_num)
        weekend_delta = 0 if latest_start.weekday() < 5 else 7 - latest_start.weekday()
        latest_start += timedelta(days=weekend_delta)
        all_time_slots.add(latest_start)
        added_days_num *= 2
    
    return sorted(list(all_time_slots)[0:5])


async def get_cancellations(
    event: EventCalendar,
    user_id
):
    oops = await check_intersections(
        user_id=user_id,
        event=event
    )
    if not oops: return None
    current_event_importance = PriorityEstimator.get_event_priority(event)
    other_events_importance = 0 if len(oops) == 0 else reduce(lambda a,b: a + b, map(lambda ev: ev.priority, oops))
    if other_events_importance > current_event_importance:
        cancelled_event_duration = event.date_time_end - event.date_time_begin
        cancelled_event_location = event.location
        cancellations_vars = await generate_event_variants(user_id, cancelled_event_duration, 
                                                        cancelled_event_location, cancelled_event_location
                                                    )
        
        earliest_begin = min(map(lambda el: el.date_time_begin, oops))
        latest_end = max(map(lambda el: el.date_time_end, oops))
        cancelled_events_duration = latest_end - earliest_begin
        earliest_location = reduce(lambda a,b: a if a.date_time_begin < b.date_time_begin else b, oops).location
        latest_location = reduce(lambda a,b: a if a.date_time_end > b.date_time_end else b, oops).location
        cancellations_vars_plan_b = await generate_event_variants(user_id, cancelled_events_duration,
                                                        earliest_location, latest_location
                                                    )

        return {
                    'most_important': [([event], variant) for variant in cancellations_vars],
                    'less_important': [(oops, variant) for variant in cancellations_vars_plan_b],
        }
    earliest_begin = min(map(lambda el: el.date_time_begin, oops))
    latest_end = max(map(lambda el: el.date_time_end, oops))
    cancelled_events_duration = latest_end - earliest_begin
    earliest_location = reduce(lambda a,b: a if a.date_time_begin < b.date_time_begin else b, oops).location
    latest_location = reduce(lambda a,b: a if a.date_time_end > b.date_time_end else b, oops).location
    cancellations_vars = await generate_event_variants(user_id, cancelled_events_duration,
                                                        earliest_location, latest_location
                                                    )
    
    cancelled_event_duration = event.date_time_end - event.date_time_begin
    cancelled_event_location = event.location
    cancellations_vars_plan_b = await generate_event_variants(user_id, cancelled_event_duration, 
                                                        cancelled_event_location, cancelled_event_location
                                                    )

    return {
                'most_important': [(oops, variant) for variant in cancellations_vars],
                'less_important': [([event], variant) for variant in cancellations_vars_plan_b],
    }