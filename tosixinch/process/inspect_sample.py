
"""Sample functions to use in ``inspect`` action."""

import json
import logging
import re
import urllib.request

logger = logging.getLogger(__name__)


def get_links(doc, match=''):
    """Print <a href> links, if regex string ``match`` matches.

    usage example:

    .. code-block:: none

        # print jpg files
        inspect=    get_links?jpg$
    """
    for text in doc.xpath('//a/@href'):
        m = re.search(match, text)
        if m:
            print(text)


def hackernews_topstories(doc):
    """Print hackernews top stories and some data, all commented out.

    Querying https://github.com/HackerNews/API.
    (So it's not using ``doc`` argumant).

    2022/04/30: quite slow (the API server itself is that way, I guess)

    usage example:

    .. code-block:: none

        # only when input is exactly the site home, no glob ('*')
        [hackernews_home]
        match=      https://news.ycombinator.com
        inspect=    hackernews_topstories
    """
    def getjson(url):
        with urllib.request.urlopen(url) as f:
            data = f.read()
        return json.loads(data.decode(encoding='utf-8'))

    url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
    topstories = getjson(url)[:50]

    title = '## TOSIXINCH: HACKERNEWS TOPSTORIES ##'
    heading = '## comments points ##'
    stories = [title, heading]

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
        stories.append(story)

    for s in stories:
        print(s)
