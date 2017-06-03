# 社畜丼ワードクラウド

- [x] ワードクラウドを出力するための基本的な環境を構築する
- [x] ローカルタイムラインからデータを取得する機能を実装する
- [x] 自動的にワードクラウドを作成、投稿する機能を実装する

### インストール
```bash
$ git clone https://github.com/mstdn-workers/wordcloud.git
$ cd wordcloud
```

http://taku910.github.io/mecab/#download から、`mecab-0.996.tar.gz` と pythonバインディング をダウンロード

```bash
$ docker build -t mstdn-workers/wordcloud .
$ docker run -d -p "8888:8888" -v "$PWD:/home/wordcloud/work/" mstdn-workers/wordcloud
```

http://localhost:8888 にアクセスします
