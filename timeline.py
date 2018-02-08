import io
import PIL
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

def with_time(time_begin, time_end, db_filename=None):
    if not db_filename:
        return __with_time_fallback(time_begin, time_end)
    
    import datetime
    from datetime import timezone
    import sqlite3
    import pickle
    
    time_range = tuple(
        time.astimezone(timezone.utc).isoformat()
        for time in (time_begin, time_end))
    
    conn = sqlite3.connect(f'file:{db_filename}?mode=ro', uri=True)
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
    return list(reversed(tl_))

def __get_media(media_file):
    if type(media_file) == str: # this is filepath
        return open(media_file, 'rb')
    if isinstance(media_file, PIL.Image.Image):
        img = io.BytesIO()
        media_file.save(img,"PNG")
        return img.getvalue()

def __media_post(media_files):
    description = None
    if type(media_files) == dict:
        description = media_files['description']
        media_file = media_files['media_file']
    else:
        media_file = media_files
    return mastodon.media_post(
        media_file=__get_media(media_file),
        mime_type='image/png',
        description=description)

def post(status, media_files=None, spoiler_text=None):
    media_ids = None
    if media_files:
        if type(media_files) == list:
            media_ids = [__media_post(media_file) for media_file in media_files]
        else:
            media_ids = [__media_post(media_files)]
    return mastodon.status_post(status=status, media_ids=media_ids, spoiler_text=spoiler_text)