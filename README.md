# 社畜丼ワードクラウド

ローカルタイムラインから一時間ぶんの投稿を取得し、ワードクラウドを作成、投稿します

### プログラムを見る・試す
```bash
$ git clone https://github.com/mstdn-workers/wordcloud.git
$ cd wordcloud
$ docker build -t mstdn-workers/wordcloud .
$ docker run -d -p "8888:8888" -v "$PWD:/work/" mstdn-workers/wordcloud
```

http://localhost:8888 にアクセスします

### インストール
systemdのユーザ権限でのUnitとして定期実行する場合

```bash
$ cp wordcloud.service wordcloud.timer ~/.config/systemd/user/
$ systemctl --user daemon-reload
$ systemctl --user start wordcloud.timer
$ systemctl --user enable wordcloud.timer
```
