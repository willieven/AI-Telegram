from datetime import datetime

def is_within_working_hours(user_settings):
    current_time = datetime.now().time()
    start_time = datetime.strptime(user_settings['WORKING_START_TIME'], '%H:%M').time()
    end_time = datetime.strptime(user_settings['WORKING_END_TIME'], '%H:%M').time()
    
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    else:  # Working hours go past midnight
        return current_time >= start_time or current_time <= end_time