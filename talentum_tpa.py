# -*- coding: utf-8 -*-
"""Talentum_TPA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aEjizoRSqD-jOJgVnWRHbgAW5MyzCkhR

#5.Streamlit
- import のところ以前のを整理^^;
"""

#%%writefile app.py
import os
import urllib
import io
import re
import sys
import time
import itertools
import requests
import json
import datetime
from dateutil import relativedelta
from datetime import date
import collections
import pandas as pd
from datetime import timedelta


def request_search(bearer_token, params, max_count):

    tweets = []
    expanded = {
        "tweets": [],
        "users": []
    }

    next_token = None

    while True:
        if next_token is not None:
            params["next_token"] = next_token

        url = "https://api.twitter.com/2/tweets/search/recent"
        encoded_params = urllib.parse.urlencode(params)
        headers = {"Authorization": f"Bearer AAAAAAAAAAAAAAAAAAAAAJ5bZwEAAAAAdlSGg9zHc8pH2IKr5HgBllUg3SA%3D3ZpLpfDZHf4Sd01v4np7rJcr3DyEXBfNTWBfpOGST30OtqGGdG"}
        res = requests.request(
            "GET", url, params=encoded_params, headers=headers)

        if res.status_code == 429:
            rate_limit_reset = int(res.headers["x-rate-limit-reset"])
            now = time.mktime(datetime.datetime.now().timetuple())
            wait_sec = int(rate_limit_reset - now)
            desc = f"Waiting for {wait_sec} seconds"
            time.sleep(1)

        elif res.status_code != 200:
            raise Exception(res.status_code, res.text)

        else:
            res_json = res.json()

            if res_json["meta"]["result_count"] == 0:
                break

            tweets += res_json["data"]
            print(f"{len(tweets)}件のツイートを取得しました。")

            if res_json.get("includes"):
                includes = res_json["includes"]
                for k, v in expanded.items():
                    if includes.get(k):
                        
                        expanded[k] += includes[k]

            next_token = res_json.get("meta").get("next_token")
            if next_token is None or len(tweets) >= max_count:
                break

    return tweets[:max_count], expanded


def export_json(fpath, data):
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def search_tweet(max_count,keyword,value):

  dt_now_jst_aware = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
  print((dt_now_jst_aware - relativedelta.relativedelta(hours=value)).isoformat())
  print((dt_now_jst_aware - relativedelta.relativedelta(minutes=1)).isoformat())


  bearer_token = "AAAAAAAAAAAAAAAAAAAAAJ5bZwEAAAAAdlSGg9zHc8pH2IKr5HgBllUg3SA%3D3ZpLpfDZHf4Sd01v4np7rJcr3DyEXBfNTWBfpOGST30OtqGGdG"
  max_count = max_count

  params = {
      "query":keyword,
      "start_time": (dt_now_jst_aware - relativedelta.relativedelta(hours=value)).isoformat(),
      "end_time": (dt_now_jst_aware - relativedelta.relativedelta(minutes=1)).isoformat(),
      "expansions": "author_id,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id",
      "max_results": "100",
      "media.fields": "duration_ms,height,media_key,preview_image_url,type,url,width,public_metrics",
      "place.fields": "contained_within,country,country_code,full_name,geo,id,name,place_type",
      "poll.fields": "duration_minutes,end_datetime,id,options,voting_status",
      "tweet.fields": "attachments,author_id,context_annotations,conversation_id,created_at,entities,geo,id,in_reply_to_user_id,lang,public_metrics,possibly_sensitive,referenced_tweets,reply_settings,source,text,withheld",
      "user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld"
  }


  tweets, expanded = request_search(bearer_token, params, max_count)


  df_tweet = pd.DataFrame()
  df_tweet_ex = pd.DataFrame()
  for i in range(0,len(tweets)):
      try:
          df_tweet.loc[i,'author_id'] = tweets[i]['author_id']
          df_tweet.loc[i,'text'] = tweets[i]['text']
          df_tweet.loc[i,'like_count'] = tweets[i]['public_metrics']['like_count']
          df_tweet.loc[i,'retweet_count'] = tweets[i]['public_metrics']['retweet_count']
          df_tweet_ex.loc[i,'name'] = expanded['users'][i]['name']
          df_tweet_ex.loc[i,'username'] = expanded['users'][i]['username']
          df_tweet_ex.loc[i,'description'] = expanded['users'][i]['description']
          df_tweet_ex.loc[i,'author_id'] = expanded['users'][i]['id']

      except:
          pass


  df_tweet = df_tweet.merge(df_tweet_ex,on='author_id',how='inner')
  df_tweet['url'] = df_tweet['username'].apply(lambda x: 'https://twitter.com/' + str(x))
  df_tweet = df_tweet[['name','username','text','description','retweet_count','like_count','url']]
  return df_tweet




import streamlit as st
import base64


pagelist = ["TPA","Analytics"]

st.set_page_config(layout="wide")
selector=st.sidebar.selectbox( "Mode",pagelist)
if selector=="TPA":
  st.title("Talentum：Talent Pool Automation")
  cnt=st.number_input('探索ツイート数の設定：0~50000',0,50000,0,step=1)
  keyword = st.text_input('人材探索キーワードの設定 半角で入力ください')
  st.text_area('分析メモ')


talent_search = st.button("Search Talent")
if talent_search :
  df_tweet = search_tweet(cnt,keyword,24*6.9)
  df_talent = df_tweet[['username','text','description','url']].rename(columns={'username':'ユーザーID','text':'ツイート本文','description':'プロフィール','url':'ツイートのURL'})
  df_talent = df_talent.groupby('ツイート本文',as_index=False).head(1)
df_talent


csv = df_talent.to_csv(index=False)  
b64 = base64.b64encode(csv.encode()).decode()
href = f'<a href="data:application/octet-stream;base64,{b64}" download="result_utf-8.csv">Download Link</a>'
st.markdown(f"人材探索データのダウンロード（csv）:  {href}", unsafe_allow_html=True)
