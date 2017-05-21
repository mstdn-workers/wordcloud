from datetime import datetime, timedelta, date
from ipywidgets import widgets
import pytz

def time_settings():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    today = now.date()
    today = jst.localize(datetime(today.year, today.month, today.day))
    datepicker = widgets.DatePicker(value=today)
    hour_end = now.timetuple().tm_hour
    time_range = widgets.FloatRangeSlider(
        value=[hour_end-1, hour_end],
        min=-6.0,
        max=24.0 + 6.0,
        step=0.1,
        continuous_update=False,
        readout=True,
        readout_format='i',
    )
    return datepicker, time_range

def time_clipping(data, today, time_begin, time_end):
    import pandas as pd
    time_begin, time_end = [today+timedelta(hours=h) for h in [time_begin, time_end]]
    df_time = data.copy()
    df_time['created_at'] = pd.to_datetime(
        df_time['created_at'].map(
            lambda s: s[1:-1] # [time] -> time
        )).map(
            lambda t: t.tz_localize('UTC').tz_convert('Asia/Tokyo')
        )

    df_ranged = df_time[
        (df_time['created_at'] >= time_begin) &
        (df_time['created_at'] < time_end)
    ]
    print(f"{today.date()} {'-'.join([t.strftime('%H:%M') for t in [time_begin, time_end]])}\n#社畜丼トレンド")

    return df_ranged