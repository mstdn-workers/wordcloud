import sys
import numpy as np
import pandas as pd

from wordcloud import WordCloud, ImageColorGenerator
from natto import MeCab

import timeline

def mecab_analysis(text):
    mecab_flags = [
        '-d /usr/lib/mecab/dic/mecab-ipadic-neologd/',
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

def create_wordcloud(text, background_image='background', slow_connection_mode=False):
    from PIL import Image

    # 環境に合わせてフォントのパスを指定する。
    #fpath = "/System/Library/Fonts/HelveticaNeue-UltraLight.otf"
    #fpath = "/Library/Fonts/ヒラギノ角ゴ Pro W3.otf"
    fpath = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"

    # ストップワードの設定
    stop_words = [
        'てる', 'いる', 'なる', 'れる', 'する', 'ある', 'ない',
        'くれる', 'やる', 'くださる', 'そう', 'せる', 'した', 'して',
        'て', 'に', 'を', 'は', 'の', 'が', 'と', 'た', 'し', 'で', 'も', 'な', 'い', 'か',
        'こと', 'これ', 'それ', 'ここ', 'もの',
        'ので', 'よう',
        'いい',
        '思う',
        '人', '気', '何',
        '私', '僕', '自分', 'やつ', 'さん', 'くん', 'ちゃん',
        '今日', '今', 'とき', 'まだ', 'もう', 'みたい',
    ]
    
    img_array = np.array(Image.open(background_image))
    
    pastel_colors = [f"hsl({hue}, 25%, 66%)" for hue in [0, 60, 120, 180]]
    def pastel_color_func(word, font_size, position, orientation, random_state=None,
                          **kwargs):
        import random
        return pastel_colors[random.randint(0, 3)]
    
    wordcloud = WordCloud(regexp=r"\w[\w']*",
                          background_color="white",
                          font_path=fpath,
                          mask=img_array,
                          color_func=pastel_color_func if slow_connection_mode else ImageColorGenerator(img_array),
                          scale=1.5,
                          stopwords=set(stop_words),
#                          max_font_size=55, 
                         ).generate(text)
    
    if slow_connection_mode:
        (wordcloud.to_image()
            .resize((400, 400), resample=Image.BOX)
            .convert(mode="P", palette=Image.ADAPTIVE, colors=8)
            .save('/tmp/wordcloud.png'))
    else:
        wordcloud.to_file("/tmp/wordcloud.png")
    
    return wordcloud

def dictFromStatus(toot):
    return dict(
        id=toot['id'],
        created_at=toot['created_at'],
        username=toot['account']['username'],
        toot=toot['content'] if toot['spoiler_text'] == '' else toot['spoiler_text']
    )

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
        lambda s: re.sub(r"＿[人 ]+＿\s*＞([^＜]+)＜\s*￣(Y\^)+Y￣", r"\1", s)
    ).map(
        lambda s: re.sub("　", "", s)
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

df_ranged = pd.DataFrame.from_records(
    [dictFromStatus(toot) for toot in timeline.with_time(*time_range)])

# 全トゥートを結合して形態素解析に流し込んで単語に分割する
wordlist = mecab_analysis(' '.join(toot_convert(filter_df(df_ranged)['toot']).iloc[::-1].tolist()))

slow_connection_mode="slow" in sys.argv

import re
#一文字ひらがな、カタカナを削除
wordlist = [w for w in wordlist if not re.match('^[あ-んーア-ンーｱ-ﾝｰ]$', w)]
#返ってきたリストを結合してワードクラウドにする
wordcloud = create_wordcloud(' '.join(wordlist), slow_connection_mode=slow_connection_mode)

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