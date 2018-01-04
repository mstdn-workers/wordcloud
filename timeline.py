from mastodon import Mastodon

#Mastodon.create_app("D's toot trends App", api_base_url = "https://mstdn-workers.com", to_file = "my_clientcred_workers.txt")
#mastodon = Mastodon(client_id="my_clientcred_workers.txt",api_base_url = "https://mstdn-workers.com")
#mastodon.log_in("mail address", "passwd",to_file = "my_usercred_workers.txt")
mastodon = Mastodon(
    client_id="my_clientcred_workers.txt",
    access_token="my_usercred_workers.txt",
    api_base_url = "https://mstdn-workers.com"
)

def __str2datetime(s):
    from datetime import datetime
    import dateutil.parser
    from pytz import timezone
    if type(s) == str:
        s = dateutil.parser.parse(s)
    return s.astimezone(timezone('Asia/Tokyo'))

def with_time(time_begin, time_end, db=False):
    if not db:
        return __with_time_fallback(time_begin, time_end)
    
    import datetime
    from datetime import timezone
    import sqlite3
    import pickle
    
    time_range = tuple(
        time.astimezone(timezone.utc).isoformat()
        for time in (time_begin, time_end))
    
    conn = sqlite3.connect('file:/db/timelines.sqlite3?mode=ro', uri=True)
    tl = list(
        pickle.loads(r[0])
        for r in conn.execute(
            'SELECT pickle FROM timeline WHERE created_at >= ? AND created_at < ?;',
            time_range))        
    conn.close()
    return tl

def __with_time_fallback(time_begin, time_end):
    tl_ = []
    from time import sleep
    max_id = None
    running = True
    while running:
        tl = mastodon.timeline(
            timeline='local',
            max_id=max_id,
            since_id=None,
            limit=40)
        max_id = tl[-1]['id']
        for toot in tl:
            created_at = __str2datetime(toot['created_at'])
            if created_at < time_begin:
                running = False
                break
            if created_at >= time_end:
                continue
            tl_.append(toot)
        if not running:
            break
        sleep(1.5)
    return reversed(tl_)

def post(status, media_file, spoiler_text=None, mime_type=None):
    media_file = mastodon.media_post(media_file=media_file, mime_type=mime_type)
    return mastodon.status_post(status=status, media_ids=[media_file], spoiler_text=spoiler_text)