from datetime import datetime, timedelta, timezone
from nmeasim.models import GpsReceiver

gps = GpsReceiver(
    date_time=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    output=('RMC', 'GGA', )
)

for i in range(3):
    gps.date_time += timedelta(seconds=1)
    print(gps.get_output())
    