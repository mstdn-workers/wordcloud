import sys
import words
import timeline

from datetime import datetime, timedelta, date
import pytz

jst = pytz.timezone('Asia/Tokyo')
now = datetime.now(jst)
today = now.date()
today = jst.localize(datetime(today.year, today.month, today.day))

hour_end = now.timetuple().tm_hour
time_range = [hour_end-1, hour_end]

def time_pair(today, time_begin, time_end):
    return [today+timedelta(hours=h) for h in [time_begin, time_end]]
[time_begin, time_end] = time_pair(today, *time_range)

def get_toot_str(today, time_begin, time_end):
    time_str = [t.strftime('%H:%M') for t in [time_begin, time_end]]
    return f"{time_begin.date()} {'-'.join(time_str)}\n#社畜丼トレンド"

time_range = time_pair(today, *time_range)
toot_str = get_toot_str(today, *time_range)
statuses = timeline.with_time(*time_range)

wordlist = words.wordlistFromStatuses(statuses)

import re
#一文字ひらがな、カタカナを削除
wordlist = [w for w in wordlist if not re.match('^[あ-んーア-ンーｱ-ﾝｰ]$', w)]

slow_connection_mode="slow" in sys.argv
#返ってきたリストを結合してワードクラウドにする
wordcloud = words.get_wordcloud_from_wordlist(wordlist, slow_connection_mode=slow_connection_mode)

if ("post" in sys.argv):
    wordcloud_img = '/tmp/wordcloud.png'
    if slow_connection_mode:
        from collections import Counter
        word_times = Counter(wordlist)
        timeline.post(
            spoiler_text=toot_str,
            media_file=wordcloud_img,
            status="\n".join(
                ["#社畜丼トレンド 低速回線モード",
                 f"{len(df_ranged)} の投稿を処理しました。",
                 "出現回数の多かった単語は以下の通りです："] + [
                    f'  "{word}": {cnt}' for word, cnt in (
                        (item[0], word_times[item[0]])
                        for item in sorted(wordcloud.words_.items(), key=lambda x:x[1], reverse=True)[:10])]
            ))
    else:
        timeline.post(status=toot_str, media_file=wordcloud_img)