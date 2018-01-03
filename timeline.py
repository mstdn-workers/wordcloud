from mastodon import Mastodon

#Mastodon.create_app("D's toot trends App", api_base_url = "https://mstdn-workers.com", to_file = "my_clientcred_workers.txt")
#mastodon = Mastodon(client_id="my_clientcred_workers.txt",api_base_url = "https://mstdn-workers.com")
#mastodon.log_in("mail address", "passwd",to_file = "my_usercred_workers.txt")
mastodon = Mastodon(
    client_id="my_clientcred_workers.txt",
    access_token="my_usercred_workers.txt",
    api_base_url = "https://mstdn-workers.com"
)

def with_time(time_begin, time_end):
    def str2datetime(s):
        from datetime import datetime
        import dateutil.parser
        from pytz import timezone
        return dateutil.parser.parse(s).astimezone(timezone('Asia/Tokyo'))
    
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
            created_at = str2datetime(toot['created_at'])
            if created_at < time_begin:
                running = False
                break
            if created_at >= time_end:
                continue
            tl_.append(toot)
        if not running:
            break
        sleep(1.5)
    return tl_

def post(status, media_file, spoiler_text=None, mime_type=None):
    media_file = mastodon.media_post(media_file=media_file, mime_type=mime_type)
    return mastodon.status_post(status=status, media_ids=[media_file], spoiler_text=spoiler_text)