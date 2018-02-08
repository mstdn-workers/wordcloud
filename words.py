import numpy as np

from wordcloud import WordCloud, ImageColorGenerator
from natto import MeCab
from functools import reduce

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

def get_content_from_status(status):
    import re
    if status['account']['username'] == 'fu': # 不適切警察
        return re.sub(r"^.*事由：([^<]+)<br />.*$", r"\1", status['content'])
    return status['spoiler_text'] or status['content']

def convert_content(content):
    import re, html
    content = re.sub('<[^>]*>', '', content)
    content = re.sub(r'https?://[^ ]+', "", content)
    content = html.unescape(content)
    content = re.sub(r"＿[人 ]+＿\s*＞([^＜]+)＜\s*￣(Y\^)+Y￣", r"\1", content)
    content = re.sub("　", "", content)
    return content

def chunks(l, n):
    """Yield successive n-sized chunks from l.
    https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks"""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def wordlist_from_statuses(statuses):
    return reduce(lambda a, b: a+b,
                  [__wordlist_from_statuses(ss) for ss in chunks(statuses, 1000)],
                  [])
def __wordlist_from_statuses(statuses):
    # 全トゥートを結合して形態素解析に流し込んで単語に分割する
    wordlist = mecab_analysis(' '.join(
        convert_content(get_content_from_status(s)) for s in statuses))
    return wordlist

def get_wordcloud_from_wordlist_for_hourly(wordlist, background_image='background', slow_connection_mode=False):
    return __get_wordcloud_from_wordlist(wordlist, background_image=background_image, slow_connection_mode=slow_connection_mode)

def get_wordcloud_from_wordlist_for_monthly(wordlist, background_image='background'):
    return __get_wordcloud_from_wordlist(wordlist, background_image=background_image)

def __get_wordcloud_from_wordlist(wordlist, background_image='background', slow_connection_mode=False):
    from PIL import Image

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
                          normalize_plurals=False,
                          background_color="white",
                          font_path=fpath,
                          mask=img_array,
                          color_func=pastel_color_func if slow_connection_mode else ImageColorGenerator(img_array),
                          scale=1.5,
                          stopwords=set(stop_words),
#                          max_font_size=55, 
                         )
    text = ' '.join(wordlist)
    words = wordcloud.process_text(text)
    wordcloud.generate_from_frequencies(words)
    
    image = wordcloud.to_image()
    if slow_connection_mode:
        image = (image
            .resize((400, 400), resample=Image.BOX)
            .convert(mode="P", palette=Image.ADAPTIVE, colors=8))
    return wordcloud, words, image