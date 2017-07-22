#!/bin/sh

DICT_INDEX=`mecab-config --libexecdir`/mecab-dict-index
DICT=`mecab-config --dicdir`/mecab-ipadic-neologd

DICT_CSV=$1
DICT_FILE=`basename "$DICT_CSV" .csv`.dic

$DICT_INDEX -d $DICT -u $DICT_FILE -f utf-8 -t utf-8 $DICT_CSV
