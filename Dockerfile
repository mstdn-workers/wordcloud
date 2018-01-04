FROM python:3.6

RUN echo 'deb http://ftp.jp.debian.org/debian unstable main' >> /etc/apt/sources.list && \
    apt update && \
    apt install -y mecab libmecab-dev mecab-ipadic-utf8 \
        sudo fonts-noto-cjk-extra fonts-ipafont -qq && \
    apt-get clean && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git && \
    ./mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -y -a && \
    rm -rf ./mecab-ipadic-neologd

ADD requirements.txt ./
RUN pip install --upgrade pip && \
    pip install jupyter && \
    pip install -r requirements.txt && \
    rm requirements.txt

ENV NB_USER wordcloud
ENV NB_UID 1000
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER

RUN mkdir /home/$NB_USER/.jupyter
COPY jupyter_notebook_config.py /home/$NB_USER/.jupyter/

EXPOSE 8888
WORKDIR /work
COPY my_clientcred_workers.txt my_usercred_workers.txt ./

COPY Wordcloud_auto.ipynb \
  timeline.py \
  words.py \
  wordcloud_auto.py \
  username.csv update_userdic.sh ./
COPY syachiku-chan.overcolored.jpg ./background

RUN chown $NB_USER:users -R /work/ /home/$NB_USER/
USER $NB_USER
RUN ./update_userdic.sh username.csv

CMD ["jupyter", "notebook"]
