from datetime import datetime
from zoneinfo import ZoneInfo 

def get_paris_timestamp():
    paris_time = datetime.now(ZoneInfo("Europe/Paris"))
    return paris_time.strftime("%Y%m%d%H%M%S")