import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
from natto import MeCab

from mastodon import Mastodon

mastodon_envs = {
    'client_id': 'MASTODON_CLIENT_ID',
    'client_secret': 'MASTODON_CLIENT_SECRET',
    'access_token': 'MASTODON_ACCESS_TOKEN',
    'api_base_url': 'MASTODON_API_BASE_URL',
}
mastodon_args = {k: os.environ[v] for k, v in mastodon_envs.items()}
mastodon = Mastodon(**mastodon_args)

def mecab_analysis(text):
    mecab_flags = [
        '-d /app/.linuxbrew/lib/mecab/dic/mecab-ipadic-neologd',
        '-u username.dic',
    ]
    t = MeCab(' '.join(mecab_flags))
    enc_text = text.strip() # MeCabに渡した文字列は必ず変数に入れておく https://shogo82148.github.io/blog/2012/12/15/mecab-python/
    t.parse('') # UnicodeDecodeError対策 http://taka-say.hateblo.jp/entry/2015/06/24/183748 
    # node = t.parseToNode(enc_text)
    output = []
    for node in t.parse(enc_text, as_nodes=True):
        if node.surface != "":  # ヘッダとフッタを除外
            word_type = node.feature.split(",")[0]
            if word_type in ["形容詞", "名詞", "副詞"]:
                output.append(node.surface)
    return output

def create_wordcloud(text, background_image='background'):

    # 環境に合わせてフォントのパスを指定する。
    #fpath = "/System/Library/Fonts/HelveticaNeue-UltraLight.otf"
    #fpath = "/Library/Fonts/ヒラギノ角ゴ Pro W3.otf"
    fpath = "/app/.fonts/NotoSansCJKjp-Medium.otf"

    # ストップワードの設定
    stop_words = [ u'てる', u'いる', u'なる', u'れる', u'する', u'ある', u'こと', u'これ', u'さん', u'して', \
             u'くれる', u'やる', u'くださる', u'そう', u'せる', u'した',  u'思う',  \
             u'それ', u'ここ', u'ちゃん', u'くん', u'', u'て',u'に',u'を',u'は',u'の', u'が', u'と', u'た', u'し', u'で', \
             u'ない', u'も', u'な', u'い', u'か', u'ので', u'よう', u'']
    
    img_array = np.array(Image.open(background_image))
    image_colors = ImageColorGenerator(img_array)
    
    wordcloud = WordCloud(regexp=r"\w[\w']*",
                          background_color="white",
                          font_path=fpath,
                          mask=img_array,
                          stopwords=set(stop_words),
#                          max_font_size=55, 
                         ).generate(text)

    plt.imshow(wordcloud.recolor(color_func=image_colors), interpolation="bilinear")
    plt.xticks([], [])
    plt.yticks([], [])
    plt.axis("off")
    
    plt.savefig("/tmp/wordcloud.png", 
                dpi=200,
                bbox_inches = 'tight',
                pad_inches = 0)

def str2datetime(s):
    from datetime import datetime
    import dateutil.parser
    from pytz import timezone
    return dateutil.parser.parse(s).astimezone(timezone('Asia/Tokyo'))

def get_ranged_toots(time_begin, time_end):
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
            tl_.append(toot2dict(toot))
        if not running:
            break
        sleep(1.5)
    df_ranged = pd.DataFrame.from_records(tl_)
    return df_ranged

def toot2dict(toot):
    t = {}
    t['id'] = toot['id']
    t['created_at'] = toot['created_at']
    t['username'] = toot['account']['username']
    t['toot'] = toot['content']
    if toot['spoiler_text'] != '':
        t['toot'] = toot['spoiler_text']
    return t

def filter_df(df):
    filter_suffix = [
        '_info', '_infom', '_information', '_material',
    ]
    return df[
        ~df['username'].map(
            lambda s:
                any([s.lower().endswith(sfx)
                     for sfx in filter_suffix])
        )
    ]

def toot_convert(toots):
    import re, html
    return toots.map(
        lambda s: re.sub('<[^>]*>', '', s)
    ).map(
        lambda s: re.sub(r'https?://[^ ]+', "", s)
    ).map(
        lambda s: html.unescape(s)
    ).map(
        lambda s: re.sub(r"＿[人 ]+＿\s+＞([^＜]+)＜\s+￣(Y\^)+Y￣", r"\1", s)
    )

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

df_ranged = get_ranged_toots(*time_range)
# 全トゥートを結合して形態素解析に流し込んで単語に分割する
wordlist = mecab_analysis(' '.join(toot_convert(filter_df(df_ranged)['toot']).iloc[::-1].tolist()))

import re
#一文字ひらがな、カタカナを削除
wordlist = [w for w in wordlist if not re.match('^[あ-んーア-ンーｱ-ﾝｰ]$', w)]
#返ってきたリストを結合してワードクラウドにする
create_wordcloud(' '.join(wordlist))

if ("post" in sys.argv):
    media_file = mastodon.media_post('/tmp/wordcloud.png')
    mastodon.status_post(status=toot_str, media_ids=[media_file])
