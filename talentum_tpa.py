# -*- coding: utf-8 -*-
"""Talentum_TPA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aEjizoRSqD-jOJgVnWRHbgAW5MyzCkhR

# 0.Initial condition
"""

!pip -q install requests tqdm
!pip -q install python-dotenv
!pip -q install gspread
!pip -q install oauth2client
!pip -q install japanize-matplotlib
!pip -q install pyyaml==5.4.1
!pip -q install pyvis
!apt-get -q -y install fonts-ipafont-gothic
!pip -q install wordcloud
!pip -q install -U spacy

# Commented out IPython magic to ensure Python compatibility.
# %%capture capt 
# !apt -q install mecab libmecab-dev mecab-ipadic-utf8
# !pip -q install mecab-python3
# !apt -q install git make curl xz-utils file
# !git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
# !echo yes | mecab-ipadic-neologd/bin/install-mecab-ipadic-neologd -n -a
# !ln -s /etc/mecabrc /usr/local/etc/mecabrc
# !pip -q install pymlask
# !pip -q install pyyaml==5.4.1
# !pip -q install "https://github.com/megagonlabs/ginza/releases/download/latest/ginza-latest.tar.gz"
# !pip -q install -U ginza ja-ginza ja-ginza_electra
# !pip -q install -U spacy

import os
import tqdm
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
import datetime
import pandas as pd
import plotly.express as px
from datetime import timedelta
import plotly.graph_objects as go
import gspread
import gspread_dataframe
from oauth2client.client import GoogleCredentials
from google.auth import default
from oauth2client.service_account import ServiceAccountCredentials
import networkx as nx
import plotly.graph_objects as go
import warnings
import tweepy
import pandas as pd
import scipy
import datetime
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib
import MeCab
import spacy
import wordcloud
from oauth2client.client import GoogleCredentials
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from requests_oauthlib import OAuth1
from dotenv import load_dotenv
from pyvis.network import Network
from collections import Counter
from mlask import MLAsk
from sklearn.preprocessing import normalize
from plotly.subplots import make_subplots
emotion_analyzer = MLAsk()

def extract_words(sent, pos_tags, stopwords):
    words = [token.lemma_ for token in sent
             if token.pos_ in pos_tags and token.lemma_ not in stopwords]
    return words

def count_cooccurrence(sents, token_length='{2,}'):
    token_pattern=f'\\b\\w{token_length}\\b'
    count_model = CountVectorizer(token_pattern=token_pattern)

    X = count_model.fit_transform(sents)
    words = count_model.get_feature_names_out()
    word_counts = np.asarray(X.sum(axis=0)).reshape(-1)

    X[X > 0] = 1
    Xc = (X.T * X) 
    return words, word_counts, Xc, X

def word_weights(words, word_counts):
    count_max = word_counts.max()
    weights = [(word, {'weight': count / count_max})
               for word, count in zip(words, word_counts)]
    return weights

def cooccurrence_weights(words, Xc, weight_cutoff):
    Xc_max = Xc.max()
    cutoff = weight_cutoff * Xc_max
    weights = [(words[i], words[j], Xc[i,j] / Xc_max)
               for i, j in zip(*Xc.nonzero()) if i < j and Xc[i,j] > cutoff]
    return weights

def create_network(words, word_counts, Xc, weight_cutoff):
    G = nx.Graph()
    
    weights_w = word_weights(words, word_counts)
    G.add_nodes_from(weights_w)
    
    weights_c = cooccurrence_weights(words, Xc, weight_cutoff)
    G.add_weighted_edges_from(weights_c)
    
    G.remove_nodes_from(list(nx.isolates(G)))
    return G

def pyplot_network(G):
    plt.figure(figsize=(15, 15))
    pos = nx.spring_layout(G, k=0.1)

    weights_n = np.array(list(nx.get_node_attributes(G, 'weight').values()))
    nx.draw_networkx_nodes(G, pos, node_size=300 * weights_n)
        
    weights_e = np.array(list(nx.get_edge_attributes(G, 'weight').values()))
    nx.draw_networkx_edges(G, pos, width=20 * weights_e)
    
    nx.draw_networkx_labels(G, pos, font_family='IPAexGothic')

    plt.axis("off")
    plt.show()

def nx2pyvis_G(G):
    pyvis_G = Network(width='800px', height='800px', notebook=True)
    for node, attrs in G.nodes(data=True):
        pyvis_G.add_node(node, title=node, size=30 * attrs['weight'])
    for node1, node2, attrs in G.edges(data=True):
        pyvis_G.add_edge(node1, node2, width=20 * attrs['weight'])
    return pyvis_G

def fav_user_check(id):
  from numpy.ma.core import identity
  bearer_token = bearer_token_input
  headers = {"Authorization": "Bearer {}".format(bearer_token)}
  params = {
            "user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld"
            }
            
  df_likes_tweet_info = pd.DataFrame()
  df_tmp = pd.DataFrame()
  for i in range(0,1):
    id = id
    url = "https://api.twitter.com/2/tweets/{}/liking_users".format(id)
    res = requests.get(url, headers=headers, params = params)
    res_text = res.text
    likes = json.loads(res_text)

    try:
      for j in range(0,len(likes['data'])):
          df_tmp['target_tweet'] = df_tweet[df_tweet['tweet_id']==id][['tweet']].reset_index(drop=True)
          df_tmp['target_tweet_day'] = df_tweet[df_tweet['tweet_id']==id][['day']].reset_index(drop=True)
          df_tmp['tweet_id'] = id
          df_tmp['regist'] = pd.read_csv(io.StringIO(likes['data'][j]['created_at']),header=None)
          #today = datetime.date.today()
          #df_tmp['use_days'] = pd.DataFrame(today - df_tmp['regist'])


          if len(pd.read_csv(io.StringIO(likes['data'][j]['name']),header=None).columns)>1:
            df_tmp['name'] = pd.read_csv(io.StringIO(likes['data'][j]['name']),header=None)[0]
          else:
            df_tmp['name'] = pd.read_csv(io.StringIO(likes['data'][j]['name']),header=None)

          df_tmp['user_name'] = pd.read_csv(io.StringIO(likes['data'][j]['username']),header=None)
          df_tmp['description'] = likes['data'][j]['description']
          df_tmp['followers'] = likes['data'][j]['public_metrics']['followers_count']
          df_tmp['follows'] = likes['data'][j]['public_metrics']['following_count']
          df_tmp['tweet_count'] = likes['data'][j]['public_metrics']['tweet_count']
          df_likes_tweet_info = pd.concat([df_likes_tweet_info,df_tmp])
          df_likes_tweet_info = df_likes_tweet_info.reset_index(drop=True)
          df_likes_tweet_info['regist_date'] = pd.to_datetime(df_likes_tweet_info['regist'], utc=True).apply(lambda x:x.tz_convert('Asia/Tokyo')).dt.date

    except:
        print('no results')

  return df_likes_tweet_info


def sentiment_nlikes(emotion,tweet_num):
  df = df_emotion_timeseries
  return df[df['emotion_jp']==emotion].sort_values('nlikes',ascending=False).head(tweet_num)


def extract_words(sent, pos_tags, stopwords):
      words = [token.lemma_ for token in sent
              if token.pos_ in pos_tags and token.lemma_ not in stopwords]
      return words

def count_cooccurrence(sents, token_length='{2,}'):
    token_pattern=f'\\b\\w{token_length}\\b'
    count_model = CountVectorizer(token_pattern=token_pattern)

    X = count_model.fit_transform(sents)
    words = count_model.get_feature_names_out()
    word_counts = np.asarray(X.sum(axis=0)).reshape(-1)

    X[X > 0] = 1
    Xc = (X.T * X) 
    return words, word_counts, Xc, X

def word_weights(words, word_counts):
    count_max = word_counts.max()
    weights = [(word, {'weight': count / count_max})
              for word, count in zip(words, word_counts)]
    return weights

def cooccurrence_weights(words, Xc, weight_cutoff):
    Xc_max = Xc.max()
    cutoff = weight_cutoff * Xc_max
    weights = [(words[i], words[j], Xc[i,j] / Xc_max)
              for i, j in zip(*Xc.nonzero()) if i < j and Xc[i,j] > cutoff]
    return weights

def create_network(words, word_counts, Xc, weight_cutoff):
    G = nx.Graph()
    
    weights_w = word_weights(words, word_counts)
    G.add_nodes_from(weights_w)
    
    weights_c = cooccurrence_weights(words, Xc, weight_cutoff)
    G.add_weighted_edges_from(weights_c)
    
    G.remove_nodes_from(list(nx.isolates(G)))
    return G

def pyplot_network(G):
    plt.figure(figsize=(15, 15))
    pos = nx.spring_layout(G, k=0.1)

    weights_n = np.array(list(nx.get_node_attributes(G, 'weight').values()))
    nx.draw_networkx_nodes(G, pos, node_size=300 * weights_n)
        
    weights_e = np.array(list(nx.get_edge_attributes(G, 'weight').values()))
    nx.draw_networkx_edges(G, pos, width=20 * weights_e)
    
    nx.draw_networkx_labels(G, pos, font_family='IPAexGothic')

    plt.axis("off")
    plt.show()

def nx2pyvis_G(G):
    pyvis_G = Network(width='800px', height='800px', notebook=True)
    for node, attrs in G.nodes(data=True):
        pyvis_G.add_node(node, title=node, size=30 * attrs['weight'])
    for node1, node2, attrs in G.edges(data=True):
        pyvis_G.add_edge(node1, node2, width=20 * attrs['weight'])
    return pyvis_G


def create_url(usernames, user_fields):
    if(any(usernames)):
        formatted_user_names = "usernames=" + ",".join(usernames)
    else:
        formatted_user_names = ""

    if(any(user_fields)):
        formatted_user_fields = "user.fields=" + ",".join(user_fields)
    else:
        formatted_user_fields = "user.fields=id,name,username"

    url = "https://api.twitter.com/2/users/by?{}&{}".format(formatted_user_names, formatted_user_fields)
    return url

def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers

  
def connect_to_endpoint(url, headers):
    response = requests.request("GET", url, headers=headers)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))
    return response.json()


def create_url(usernames, user_fields):
    if(any(usernames)):
        formatted_user_names = "usernames=" + ",".join(usernames)
    else:
        formatted_user_names = ""

    if(any(user_fields)):
        formatted_user_fields = "user.fields=" + ",".join(user_fields)
    else:
        formatted_user_fields = "user.fields=id,name,username"

    url = "https://api.twitter.com/2/users/by?{}&{}".format(formatted_user_names, formatted_user_fields)
    return url

def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers

  
def connect_to_endpoint(url, headers):
    response = requests.request("GET", url, headers=headers)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))
    return response.json()

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
            for _ in tqdm.trange(wait_sec, desc=desc):
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
          #df_tweet.loc[i,'created_at'] = pd.to_datetime(tweets[i]['created_at']) + datetime.timedelta(hours=9)
          df_tweet.loc[i,'author_id'] = tweets[i]['author_id']
          df_tweet.loc[i,'text'] = tweets[i]['text']
          #df_tweet.loc[i,'tweet_id'] = tweets[i]['id']
          df_tweet.loc[i,'like_count'] = tweets[i]['public_metrics']['like_count']
          df_tweet.loc[i,'retweet_count'] = tweets[i]['public_metrics']['retweet_count']
          #df_tweet.loc[i,'reply_count'] = tweets[i]['public_metrics']['reply_count']

          #df_tweet_ex.loc[i,'regist_date'] = pd.to_datetime(expanded['users'][i]['created_at']) + datetime.timedelta(hours=9)
          df_tweet_ex.loc[i,'name'] = expanded['users'][i]['name']
          df_tweet_ex.loc[i,'username'] = expanded['users'][i]['username']
          df_tweet_ex.loc[i,'description'] = expanded['users'][i]['description']
          #df_tweet_ex.loc[i,'following_count'] = expanded['users'][i]['public_metrics']['following_count']
          #df_tweet_ex.loc[i,'followers_count'] = expanded['users'][i]['public_metrics']['followers_count']
          #df_tweet_ex.loc[i,'listed_count'] = expanded['users'][i]['public_metrics']['listed_count']
          #df_tweet_ex.loc[i,'tweet_count'] = expanded['users'][i]['public_metrics']['tweet_count']
          #df_tweet_ex.loc[i,'prof_link'] = expanded['users'][i]['url']
          #df_tweet_ex.loc[i,'pinned_tweet_id'] = expanded['users'][i]['pinned_tweet_id']
          df_tweet_ex.loc[i,'author_id'] = expanded['users'][i]['id']

      except:
          pass

  # for i in range(0,len(tweets)):
  #     try:
  #         df_tweet_ex.loc[i,'regist_date'] = pd.to_datetime(expanded['users'][i]['created_at']) + datetime.timedelta(hours=9)
  #         df_tweet_ex.loc[i,'username'] = expanded['users'][i]['username']
  #         df_tweet_ex.loc[i,'description'] = expanded['users'][i]['description']
  #         df_tweet_ex.loc[i,'following_count'] = expanded['users'][i]['public_metrics']['following_count']
  #         df_tweet_ex.loc[i,'followers_count'] = expanded['users'][i]['public_metrics']['followers_count']
  #         df_tweet_ex.loc[i,'listed_count'] = expanded['users'][i]['public_metrics']['listed_count']
  #         df_tweet_ex.loc[i,'tweet_count'] = expanded['users'][i]['public_metrics']['tweet_count']
  #         df_tweet_ex.loc[i,'prof_link'] = expanded['users'][i]['url']
  #         df_tweet_ex.loc[i,'pinned_tweet_id'] = expanded['users'][i]['pinned_tweet_id']
  #         df_tweet_ex.loc[i,'author_id'] = expanded['users'][i]['id']
  #     except:
  #         pass

  df_tweet = df_tweet.merge(df_tweet_ex,on='author_id',how='inner')


  # df_tweet['date'] = pd.to_datetime(df_tweet['created_at'])
  # df_tweet['day'] = pd.to_datetime(df_tweet['created_at']).dt.date
  # df_tweet['hour'] = pd.to_datetime(df_tweet['created_at']).dt.hour
  # df_tweet['min'] = pd.to_datetime(df_tweet['created_at']).dt.minute
  #df_tweet = df_tweet.groupby('text',as_index=False).head(1).reset_index(drop=True)
  df_tweet['url'] = df_tweet['username'].apply(lambda x: 'https://twitter.com/' + str(x))
  df_tweet = df_tweet[['name','username','text','description','retweet_count','like_count','url']]
  return df_tweet

"""#5.Streamlit
- import のところ以前のを整理^^;

"""

!pip install streamlit

# Commented out IPython magic to ensure Python compatibility.
# %%writefile app.py
# import os
# import tqdm
# import urllib
# import io
# import re
# import sys
# import time
# import itertools
# import requests
# import json
# import datetime
# from dateutil import relativedelta
# from datetime import date
# import collections
# import datetime
# import pandas as pd
# import plotly.express as px
# from datetime import timedelta
# import plotly.graph_objects as go
# import gspread
# import gspread_dataframe
# from oauth2client.client import GoogleCredentials
# from google.auth import default
# from oauth2client.service_account import ServiceAccountCredentials
# import networkx as nx
# import plotly.graph_objects as go
# import warnings
# import tweepy
# import pandas as pd
# import scipy
# import datetime
# import plotly.express as px
# import numpy as np
# import matplotlib.pyplot as plt
# 
# 
# 
# def request_search(bearer_token, params, max_count):
# 
#     tweets = []
#     expanded = {
#         "tweets": [],
#         "users": []
#     }
# 
#     next_token = None
# 
#     while True:
#         if next_token is not None:
#             params["next_token"] = next_token
# 
#         url = "https://api.twitter.com/2/tweets/search/recent"
#         encoded_params = urllib.parse.urlencode(params)
#         headers = {"Authorization": f"Bearer AAAAAAAAAAAAAAAAAAAAAJ5bZwEAAAAAdlSGg9zHc8pH2IKr5HgBllUg3SA%3D3ZpLpfDZHf4Sd01v4np7rJcr3DyEXBfNTWBfpOGST30OtqGGdG"}
#         res = requests.request(
#             "GET", url, params=encoded_params, headers=headers)
# 
#         if res.status_code == 429:
#             rate_limit_reset = int(res.headers["x-rate-limit-reset"])
#             now = time.mktime(datetime.datetime.now().timetuple())
#             wait_sec = int(rate_limit_reset - now)
#             desc = f"Waiting for {wait_sec} seconds"
#             for _ in tqdm.trange(wait_sec, desc=desc):
#                 time.sleep(1)
# 
#         elif res.status_code != 200:
#             raise Exception(res.status_code, res.text)
# 
#         else:
#             res_json = res.json()
# 
#             if res_json["meta"]["result_count"] == 0:
#                 break
# 
#             tweets += res_json["data"]
#             print(f"{len(tweets)}件のツイートを取得しました。")
# 
#             if res_json.get("includes"):
#                 includes = res_json["includes"]
#                 for k, v in expanded.items():
#                     if includes.get(k):
#                         
#                         expanded[k] += includes[k]
# 
#             next_token = res_json.get("meta").get("next_token")
#             if next_token is None or len(tweets) >= max_count:
#                 break
# 
#     return tweets[:max_count], expanded
# 
# 
# def export_json(fpath, data):
#     with open(fpath, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False)
# 
# 
# def search_tweet(max_count,keyword,value):
# 
#   dt_now_jst_aware = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
#   print((dt_now_jst_aware - relativedelta.relativedelta(hours=value)).isoformat())
#   print((dt_now_jst_aware - relativedelta.relativedelta(minutes=1)).isoformat())
# 
# 
#   bearer_token = "AAAAAAAAAAAAAAAAAAAAAJ5bZwEAAAAAdlSGg9zHc8pH2IKr5HgBllUg3SA%3D3ZpLpfDZHf4Sd01v4np7rJcr3DyEXBfNTWBfpOGST30OtqGGdG"
#   max_count = max_count
# 
#   params = {
#       "query":keyword,
#       "start_time": (dt_now_jst_aware - relativedelta.relativedelta(hours=value)).isoformat(),
#       "end_time": (dt_now_jst_aware - relativedelta.relativedelta(minutes=1)).isoformat(),
#       "expansions": "author_id,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id",
#       "max_results": "100",
#       "media.fields": "duration_ms,height,media_key,preview_image_url,type,url,width,public_metrics",
#       "place.fields": "contained_within,country,country_code,full_name,geo,id,name,place_type",
#       "poll.fields": "duration_minutes,end_datetime,id,options,voting_status",
#       "tweet.fields": "attachments,author_id,context_annotations,conversation_id,created_at,entities,geo,id,in_reply_to_user_id,lang,public_metrics,possibly_sensitive,referenced_tweets,reply_settings,source,text,withheld",
#       "user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld"
#   }
# 
# 
#   tweets, expanded = request_search(bearer_token, params, max_count)
# 
# 
#   df_tweet = pd.DataFrame()
#   df_tweet_ex = pd.DataFrame()
#   for i in range(0,len(tweets)):
#       try:
#           #df_tweet.loc[i,'created_at'] = pd.to_datetime(tweets[i]['created_at']) + datetime.timedelta(hours=9)
#           df_tweet.loc[i,'author_id'] = tweets[i]['author_id']
#           df_tweet.loc[i,'text'] = tweets[i]['text']
#           #df_tweet.loc[i,'tweet_id'] = tweets[i]['id']
#           df_tweet.loc[i,'like_count'] = tweets[i]['public_metrics']['like_count']
#           df_tweet.loc[i,'retweet_count'] = tweets[i]['public_metrics']['retweet_count']
#           #df_tweet.loc[i,'reply_count'] = tweets[i]['public_metrics']['reply_count']
# 
#           #df_tweet_ex.loc[i,'regist_date'] = pd.to_datetime(expanded['users'][i]['created_at']) + datetime.timedelta(hours=9)
#           df_tweet_ex.loc[i,'name'] = expanded['users'][i]['name']
#           df_tweet_ex.loc[i,'username'] = expanded['users'][i]['username']
#           df_tweet_ex.loc[i,'description'] = expanded['users'][i]['description']
#           #df_tweet_ex.loc[i,'following_count'] = expanded['users'][i]['public_metrics']['following_count']
#           #df_tweet_ex.loc[i,'followers_count'] = expanded['users'][i]['public_metrics']['followers_count']
#           #df_tweet_ex.loc[i,'listed_count'] = expanded['users'][i]['public_metrics']['listed_count']
#           #df_tweet_ex.loc[i,'tweet_count'] = expanded['users'][i]['public_metrics']['tweet_count']
#           #df_tweet_ex.loc[i,'prof_link'] = expanded['users'][i]['url']
#           #df_tweet_ex.loc[i,'pinned_tweet_id'] = expanded['users'][i]['pinned_tweet_id']
#           df_tweet_ex.loc[i,'author_id'] = expanded['users'][i]['id']
# 
#       except:
#           pass
# 
# 
#   df_tweet = df_tweet.merge(df_tweet_ex,on='author_id',how='inner')
#   df_tweet['url'] = df_tweet['username'].apply(lambda x: 'https://twitter.com/' + str(x))
#   df_tweet = df_tweet[['name','username','text','description','retweet_count','like_count','url']]
#   return df_tweet
# 
# 
# 
# 
# import streamlit as st
# import base64
# st.set_page_config(layout="wide")
# st.title("Talentum：Talent Pool Automation")
# cnt=st.number_input('探索ツイート数の設定：0~50000',0,50000,0,step=1)
# keyword = st.text_input('人材探索キーワードの設定 半角で入力ください')
# st.text_area('分析メモ')
# 
# 
# talent_search = st.button("Search Talent")
# if talent_search :
#   df_tweet = search_tweet(cnt,keyword,24*6.9)
#   df_talent = df_tweet[['username','text','description','url']].rename(columns={'username':'ユーザーID','text':'ツイート本文','description':'プロフィール','url':'ツイートのURL'})
#   df_talent = df_talent.groupby('ツイート本文',as_index=False).head(1)
# df_talent
# 
# 
# csv = df_talent.to_csv(index=False)  
# b64 = base64.b64encode(csv.encode()).decode()
# href = f'<a href="data:application/octet-stream;base64,{b64}" download="result_utf-8.csv">Download Link</a>'
# st.markdown(f"人材探索データのダウンロード（csv）:  {href}", unsafe_allow_html=True)
# 
#

from google.colab import files
files.view("/content")
files.view("app.py")

!streamlit run app.py & sleep 3 && npx localtunnel --port 8501