
"""Fetch urls from news site pages.

Intended to make easier to build ``urls.txt``.

Not developed now.
"""

import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

FL_SOCIALNEWS = '## TOSIXINCH: SOCIALNEWS URLS ##'


def socialnews(arg):
    if arg == 'hackernews':
        return print_news(hackernews())


def hackernews():
    # https://github.com/HackerNews/API
    def getjson(url):
        with urllib.request.urlopen(url) as f:
            data = f.read()
        return json.loads(data.decode(encoding='utf-8'))

    url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
    topstories = getjson(url)[:50]

    stories = [FL_SOCIALNEWS, ]
    for topstory in topstories:
        urlfmt = 'https://hacker-news.firebaseio.com/v0/item/%s.json'
        url = urlfmt % str(topstory)
        st = getjson(url)
        hnurl = 'https://news.ycombinator.com/item?id=%s' % str(topstory)
        if st.get('descendants', 0) < 5 or st['score'] < 5:
            continue
        story = '# %4s %4s\n# %s\n# %s\n# %s\n' % (
                st.get('descendants', '0'), st['score'], st['title'],
                st.get('url', ''), hnurl)
        # print(story)
        stories.append(story)
    return stories


def print_news(stories):
    for s in stories:
        print(s)
