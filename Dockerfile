FROM python:3.6

RUN echo 'APT::Default-Release "stable";' > /etc/apt/apt.conf.d/99target && \
    echo 'deb http://ftp.jp.debian.org/debian unstable main contrib non-free' >> /etc/apt/sources.list && \
    echo 'deb http://ftp.jp.debian.org/debian jessie main contrib non-free' >> /etc/apt/sources.list && \
    apt update && \
    apt upgrade -y && \
    apt install -y mecab libmecab-dev mecab-ipadic-utf8 \
        sudo font-manager fonts-noto fonts-noto-cjk/unstable fonts-ipafont -qq && \
    apt-get clean && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
  pip install jupyter \
  pandas matplotlib scipy seaborn scikit-learn scikit-image \
  sympy cython patsy numba bokeh Mastodon.py \
  pivottablejs ipywidgets wordcloud mecab-python3 \
  sqlalchemy emoji --upgrade && \
    jupyter nbextension enable --py --sys-prefix widgetsnbextension

RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git /usr/src/mecab-ipadic-neologd && \
    /usr/src/mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -y -a

ENV NB_USER wordcloud
ENV NB_UID 1000
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER

USER $NB_USER

RUN mkdir /home/$NB_USER/work && \
    mkdir /home/$NB_USER/.jupyter && \
    jupyter nbextension enable --py widgetsnbextension

EXPOSE 8888
COPY jupyter_notebook_config.py /home/$NB_USER/.jupyter/
WORKDIR /home/$NB_USER/work

COPY wordcloud_auto.py ./
COPY my_clientcred_workers.txt my_usercred_workers.txt username.dic ./
COPY syachiku-chan.overcolored.jpg ./background

CMD ["jupyter", "notebook"]
