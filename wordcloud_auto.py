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

def get_wordcount_lines(wordcount):
    from operator import itemgetter
    return (
        "出現回数の多かった単語は以下の通りです：",
        *(f'  "{word}": {cnt}'
          for word, cnt in sorted(
              wordcount.items(),
              key=itemgetter(1),
              reverse=True)[:10]))

def get_status_params(today, time_range, statuses, detail_texts, slow_connection_mode, wordcloud, wordcount):
    wordcloud_img = '/tmp/wordcloud.png'
    status_str_lines = [get_time_str(today, time_range)]
    status_str_lines.append("#社畜丼トレンド" if not slow_connection_mode else "#社畜丼トレンド 低速回線モード")
    status_str_lines.append(f"{len(statuses)} の投稿を処理しました。")
    status_str_lines.extend(detail_texts)
    if slow_connection_mode:
        status_str_lines.extend(get_wordcount_lines(wordcount))
    
    status_params = dict(
        media_file=wordcloud_img,
        status="\n".join(status_str_lines)
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

def is_spam(status):
    spam_accounts = ['yukimama']
    spam_account_name_suffix = [
        '_info', '_infom', '_information', '_material',
    ]
    username = status['account']['username']
    return username in spam_accounts or \
        any(username.lower().endswith(sfx) for sfx in spam_account_name_suffix)

def is_trend(status):
    app = status['application']
    return app['name'] == "D's toot trends App" if app else False

def filterfalse_with_count(seq, *preds):
    filter_result = []
    counts = [0] * len(preds)
    for item in seq:
        for i, pred in enumerate(preds):
            if pred(item):
                counts[i] += 1
                break
        else:
            filter_result.append(item)
    return (filter_result, *counts)

def filter_statuses_with_detail_texts(statuses):
    detail_texts = []
    statuses, spam_cnt, self_cnt = filterfalse_with_count(statuses, is_spam, is_trend)
    if spam_cnt > 0:
        detail_texts.append(f"スパムとして{spam_cnt}の投稿を除外しました。")
    if self_cnt > 0:
        detail_texts.append(f"社畜丼トレンド自身の{f'{self_cnt}個の' if self_cnt > 1 else ''}投稿を除外しました。")
    return statuses, detail_texts

statuses, detail_texts = filter_statuses_with_detail_texts(statuses)
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
        detail_texts,
        slow_connection_mode,
        wordcloud, wordcount))