import numpy as np
import pandas as pd

from wordcloud import WordCloud, ImageColorGenerator
from natto import MeCab

def mecab_analysis(text):
    import os
    mecab_flags = [
        f'-d {os.popen("mecab-config --dicdir").read().strip()}/mecab-ipadic-neologd/',
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

def wordlistFromStatuses(statuses):
    df_ranged = pd.DataFrame.from_records(
    [dictFromStatus(s) for s in statuses])

    # 全トゥートを結合して形態素解析に流し込んで単語に分割する
    wordlist = mecab_analysis(' '.join(toot_convert(filter_df(df_ranged)['toot']).tolist()))
    return wordlist

def get_wordcloud_from_wordlist(wordlist, background_image='background', slow_connection_mode=False):
    from PIL import Image

    fpath = "./GDhwGoJA-OTF112b2.otf"

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
    
    def white_color_func(word, font_size, position, orientation, random_state=None,
                          **kwargs):
        return "white"
    
    wordcloud = WordCloud(regexp=r"\w[\w']*",
                          background_color="rgb(0,116,89)",
                          font_path=fpath,
                          mask=img_array,
                          color_func=white_color_func,
                          scale=1.5,
                          stopwords=set(stop_words),
#                          max_font_size=55, 
                         ).generate(' '.join(wordlist))
    
    if slow_connection_mode:
        (wordcloud.to_image()
            .resize((400, 400), resample=Image.BOX)
            .convert(mode="P", palette=Image.ADAPTIVE, colors=8)
            .save('/tmp/wordcloud.png'))
    else:
        wordcloud.to_file("/tmp/wordcloud.png")
    
    return wordcloud