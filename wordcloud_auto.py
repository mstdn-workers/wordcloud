import sys
import words
import timeline

from datetime import datetime, timedelta, date
import pytz

def time_pair(today, hour_begin, hour_end):
    return tuple(today+timedelta(hours=h) for h in [hour_begin, hour_end])

def get_time_str(today, time_range):
    time_str = [t.strftime('%H:%M') for t in time_range]
    time_begin = time_range[0]
    return f"{time_begin.date()} {'-'.join(time_str)}"

def get_toot_str(today, time_range):
    return "\n".join((get_time_str(today, time_range), "#社畜丼トレンド"))

jst = pytz.timezone('Asia/Tokyo')
now = datetime.now(jst)
today = now.date()
today = jst.localize(datetime(today.year, today.month, today.day))

hour_end = now.timetuple().tm_hour
hour_pair = [hour_end-1, hour_end]

time_range = time_pair(today, *hour_pair)
toot_str = get_toot_str(today, time_range)

use_database = "db" in sys.argv

statuses = timeline.with_time(*time_range, use_database)
wordlist = words.wordlistFromStatuses(statuses)

import re
#一文字ひらがな、カタカナを削除
wordlist = [w for w in wordlist if not re.match('^[あ-んーア-ンーｱ-ﾝｰ]$', w)]

slow_connection_mode="slow" in sys.argv
#返ってきたリストを結合してワードクラウドにする
wordcloud, wordcount = words.get_wordcloud_from_wordlist(
    wordlist,
    slow_connection_mode=slow_connection_mode)

if ("post" in sys.argv):
    wordcloud_img = '/tmp/wordcloud.png'
    if slow_connection_mode: 
        from operator import itemgetter
        timeline.post(
            media_file=wordcloud_img,
            status="\n".join(
                [toot_str + " 低速回線モード",
                 f"{len(statuses)} の投稿を処理しました。",
                 "出現回数の多かった単語は以下の通りです："] + \
                [f'  "{word}": {cnt}'
                 for word, cnt in sorted(
                     wordcount.items(),
                     key=itemgetter(1),
                     reverse=True)[:10]]
            ))
    else:
        timeline.post(status=toot_str, media_file=wordcloud_img)