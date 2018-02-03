import sys
import argparse
import words
import timeline

from enum import Enum, auto
from datetime import datetime, timedelta, date
import pytz

def get_timepair_from_hourpair(today, hour_begin, hour_end):
    return tuple(today+timedelta(hours=h) for h in [hour_begin, hour_end])

def get_time_str_for_hourly(time_range):
    time_begin, time_end = time_range
    time_formats = ['%Y/%m/%d %H:%M'] * 2
    if time_begin.year == time_end.year:
        time_formats[1] = '%m/%d %H:%M'
    if time_begin.date() == time_end.date():
        time_formats[1] = '%H:%M'
    return ' - '.join(t.strftime(f) for f, t in zip(time_formats, time_range))

def get_time_str_for_monthly(time_range):
    return ' - '.join(t.strftime('%Y/%m/%d') for t in time_range)

def get_wordcount_lines(wordcount):
    from operator import itemgetter
    return (
        "出現回数の多かった単語は以下の通りです：",
        *(f'  "{word}": {cnt}'
          for word, cnt in sorted(
              wordcount.items(),
              key=itemgetter(1),
              reverse=True)[:10]))

def get_status_params_for_hourly(
        today, time_range,
        statuses, enough_words, detail_texts, message,
        slow_connection_mode, wordcloud=None, wordcount=dict()):
    return __get_status_params(
        TimeSpanMode.HOURLY,
        today, time_range,
        statuses, enough_words, detail_texts, message,
        slow_connection_mode, wordcloud, wordcount
    )

def get_status_params_for_monthly(
        today, time_range,
        statuses, enough_words, detail_texts, message,
        wordcloud=None, wordcount=dict()):
    return __get_status_params(
        TimeSpanMode.MONTHLY,
        today, time_range,
        statuses, enough_words, detail_texts, message,
        slow_connection_mode=False, wordcloud=wordcloud, wordcount=wordcount
    )

def __get_status_params(
        timespan_mode,
        today, time_range,
        statuses, enough_words, detail_texts, message,
        slow_connection_mode, wordcloud, wordcount):
    wordcloud_img = '/tmp/wordcloud.png'
    if timespan_mode == TimeSpanMode.HOURLY:
        status_str_lines = [get_time_str_for_hourly(time_range)]
        status_str_lines.append("#社畜丼トレンド" if not slow_connection_mode else "#社畜丼トレンド 低速回線モード")
    elif timespan_mode == TimeSpanMode.MONTHLY:
        status_str_lines = [get_time_str_for_monthly(time_range)]
        status_str_lines.append("#社畜丼トレンド")
        status_str_lines.append("#月刊トレンド")
    if message:
        status_str_lines.append(message)
    status_str_lines.extend(detail_texts)
    status_str_lines.append(f"{len(statuses)} の投稿を処理しました。")
    if slow_connection_mode and wordcount:
        status_str_lines.extend(get_wordcount_lines(wordcount))
    
    if enough_words:
        status_params = dict(
            media_file=wordcloud_img,
            status="\n".join(status_str_lines)
        )
    else:
        status_str_lines.append("トレンド画像を生成するために充分な単語数がありません")
        status_params = dict(
            status="\n".join(status_str_lines)
        )
    return status_params

def zen_alnum_normalize(c):
    if "０" <= c <= "９": return chr(ord(c) - ord("０") + ord('0'))
    if "Ａ" <= c <= "ｚ": return chr(ord(c) - ord("Ａ") + ord('A'))
    return c

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

def is_some_bots(status):
    app = status['application']
    if not app: return False
    return any(app['name'] == name for name in ['オフ会カレンダー', 'off_bot', '安価bot'])

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
    statuses, spam_cnt, self_cnt, some_cnt = filterfalse_with_count(statuses, is_spam, is_trend, is_some_bots)
    if spam_cnt > 0:
        detail_texts.append(f"スパムとして{spam_cnt}の投稿を除外しました。")
    if self_cnt > 0:
        detail_texts.append(f"社畜丼トレンド自身の{f'{self_cnt}個の' if self_cnt > 1 else ''}投稿を除外しました。")
    # some_cnt 幾つかのbotの投稿は無言で消し去る
    return statuses, detail_texts

def convert_wordlist(wordlist):
    import re
    #一文字ひらがな、カタカナを削除
    wordlist = (w for w in wordlist if not re.match('^[あ-んーア-ンーｱ-ﾝｰ]$', w))
    #全角数字とアルファベットを半角へ
    wordlist = ("".join(zen_alnum_normalize(c) for c in w) for w in wordlist)
    return list(wordlist)

def enough_words(wordlist):
    return len(set(wordlist)) > 2

class TimeSpanMode(Enum):
    HOURLY = auto()
    MONTHLY = auto()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', '--use-database', metavar='DATABASE',
                        help='get statuses from database; DATABASE is path to sqlite3 database file like "/db/timeline.sqlite3"')
    parser.add_argument('--post', action='store_true',
                        help="to post status if not interactive-mode else to generate status_params only")
    parser.add_argument('--message', help="additional message")
    
    subparsers = parser.add_subparsers()
    parser_hourly = subparsers.add_parser('hourly', help='see `hourly -h`', aliases=['h'])
    parser_hourly.set_defaults(timespan_mode=TimeSpanMode.HOURLY)
    
    hour_exclusive_group = parser_hourly.add_argument_group('hour').add_mutually_exclusive_group()
    hour_exclusive_group.add_argument('--since-hour', metavar='SINCE_HOUR', type=int,
                                      help="generate timeline trend wordcloud with [SINCE_HOUR, SINCE_HOUR+1]")
    hour_exclusive_group.add_argument('--range', '--hour-range', metavar=('SINCE_HOUR', 'UNTIL_HOUR'), nargs=2, type=int)
    parser_hourly.add_argument('--slow', '--slow-connection-mode', action='store_true',
                               help="run as slow-connection-mode. less image size and fallback text.")
    
    parser_monthly = subparsers.add_parser('monthly', help='see `monthly -h`', aliases=['m'])
    parser_monthly.set_defaults(timespan_mode=TimeSpanMode.MONTHLY)
    parser_monthly.add_argument('--try-this-month', action='store_true',
                               help="generate for this month; not prev month")
    
    args = parser.parse_args()
    
    if not hasattr(args, 'timespan_mode'):
        parser.print_help()
        parser.exit()
    
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    today = now.date()
    if args.timespan_mode == TimeSpanMode.HOURLY:
        today = jst.localize(datetime(today.year, today.month, today.day))
        hour_end = now.timetuple().tm_hour
        if args.since_hour != None:
            hour_pair = [args.since_hour, args.since_hour+1]
        elif args.range:
            hour_pair = args.range
        else:
            hour_pair = [hour_end-1, hour_end]

        time_range = get_timepair_from_hourpair(today, *hour_pair)
    elif args.timespan_mode == TimeSpanMode.MONTHLY:
        if not args.try_this_month:
            this_month = jst.localize(datetime(today.year, today.month, 1))
            yesterday_of_1 = this_month - timedelta(days=1)
            prev_month = jst.localize(datetime(yesterday_of_1.year, yesterday_of_1.month, 1))
        else:
            prev_month = jst.localize(datetime(today.year, today.month, 1))
            next_1 = prev_month + timedelta(days=31)
            this_month = jst.localize(datetime(next_1.year, next_1.month, 1))
        time_range = prev_month, this_month
    
    statuses = timeline.with_time(*time_range, args.db)
    statuses, detail_texts = filter_statuses_with_detail_texts(statuses)
    wordlist = words.wordlist_from_statuses(statuses)
    wordlist = convert_wordlist(wordlist)
    
    enough = enough_words(wordlist)
    
    wordcloud, wordcount = None, None
    
    if enough:
        if args.timespan_mode == TimeSpanMode.HOURLY:
                #返ってきたリストを結合してワードクラウドにする
                wordcloud, wordcount = words.get_wordcloud_from_wordlist_for_hourly(
                    wordlist,
                    slow_connection_mode=args.slow)
        elif args.timespan_mode == TimeSpanMode.MONTHLY:
            wordcloud, wordcount = words.get_wordcloud_from_wordlist_for_monthly(
                    wordlist,
                    background_image='./redbull.png')
    
    # インタラクティブモードにするのに即投稿したいわけがないので
    # postオプションが指定されたときはパラメータの生成のみを行う
    if args.post:
        if args.timespan_mode == TimeSpanMode.HOURLY:
            status_params = get_status_params_for_hourly(
                today, time_range,
                statuses,
                enough,
                detail_texts,
                args.message,
                args.slow,
                wordcloud, wordcount)
        elif args.timespan_mode == TimeSpanMode.MONTHLY:
            status_params = get_status_params_for_monthly(
                today, time_range,
                statuses,
                enough,
                detail_texts,
                args.message,
                wordcloud, wordcount)
        
        if not sys.flags.interactive:
            timeline.post(**status_params)