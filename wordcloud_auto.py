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

def get_fallback_text(statuses, wordcloud, wordcount):
    from operator import itemgetter
    return "\n".join(
        ["低速回線モード",
         f"{len(statuses)} の投稿を処理しました。",
         "出現回数の多かった単語は以下の通りです："] + \
        [f'  "{word}": {cnt}'
         for word, cnt in sorted(
             wordcount.items(),
             key=itemgetter(1),
             reverse=True)[:10]])

def get_status_params(today, time_range, statuses, slow_connection_mode, wordcloud, wordcount):
    wordcloud_img = '/tmp/wordcloud.png'
    status_str = get_time_str(today, time_range) + "\n" + "#社畜丼トレンド"
    if slow_connection_mode:
        status_str = status_str + " " + get_fallback_text(statuses, wordcloud, wordcount)
    
    status_params = dict(
        media_file=wordcloud_img,
        status=status_str
    )
    return status_params

def zen_alnum_normalize(c):
    if "０" <= c <= "９": return chr(ord(c) - ord("０") + ord('0'))
    if "Ａ" <= c <= "ｚ": return chr(ord(c) - ord("Ａ") + ord('A'))
    return c

jst = pytz.timezone('Asia/Tokyo')
now = datetime.now(jst)
today = now.date()
today = jst.localize(datetime(today.year, today.month, today.day))

hour_end = now.timetuple().tm_hour
hour_pair = [hour_end-1, hour_end]

time_range = time_pair(today, *hour_pair)

use_database = "db" in sys.argv

statuses = timeline.with_time(*time_range, use_database)
wordlist = words.wordlist_from_statuses(statuses)

import re
#一文字ひらがな、カタカナを削除
wordlist = [w for w in wordlist if not re.match('^[あ-んーア-ンーｱ-ﾝｰ]$', w)]
#全角数字とアルファベットを半角へ
wordlist = ["".join(zen_alnum_normalize(c) for c in w) for w in wordlist]

slow_connection_mode="slow" in sys.argv
#返ってきたリストを結合してワードクラウドにする
wordcloud, wordcount = words.get_wordcloud_from_wordlist(
    wordlist,
    slow_connection_mode=slow_connection_mode)

if ("post" in sys.argv):
    timeline.post(**get_status_params(
        today, time_range,
        statuses,
        slow_connection_mode,
        wordcloud, wordcount))