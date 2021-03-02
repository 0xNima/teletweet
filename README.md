# teletweet
A project to sends real-time tweets to telegram endpoint
.
This project uses twitter v2 api to get real-time tweets. thus you should prepair you api key from [here](https://developer.twitter.com/en/apply-for-access).


## Getting Started
### Prerequisites
Since twitter standrad api key has some limitations like rule limits(25 rule per api key), to apply more rules per api key, we'll concatinate new rule with previous rules each time. Thus we are using redis backend to store rules, You can install redis from [here](https://redis.io/download). 

### Installing
clone the code and install packages:
```
git clone https://github.com/object-ptr/teletweet.git
cd teletweet
pip install -r requirements.txt
```

### Configuring
open the config.py file and enter required keys and tokens:

```
TWITTER_API_KEY = ""

TWITTER_API_SECRET_KEY = ""

TWITTER_BEARER_TOKEN = ""

TARGET_TELEGRAM_ENDPOINT = ""   # either chat_id<int>, username<str> or channel username<str>

TELEGRAM_BOT_TOKEN = ""
```

console logging and file logging are enable by default. You can set the log file's path as you want. To disable each logging, simply set `False`:
```
FILE_LOGGING_ENABLE = True

CONSOLE_LOGGING_ENABLE = True

LOG_FILE = "teletweet.log"
``` 
Modify redis configs as you needed:
```
REDIS_BACKEND_CONFIG = {
    "host": "localhost",
    "db": 0,
    "port": "6379",
    "username": "",
    "password": "",
}
```
You can apply additional filters to get appropriate tweets by setting manual rules to `MANUAL_RULE`. You cand read more about building twitter rules [here](https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule).

By default we use four rule:
```
GET_VERIFIED_TWEETS = None

GET_REPLY_TWEETS = False

GET_QUOTE_TWEETS = False

GET_RETWEET_TWEETS = False
```
Above params converted to `-is:reply -is:quote -is:retweet`. This rule doesn't get reply, quote and retweets. Feel free to change this params to create your own rule. 
### Notice
`None` is different from `False`. When you assign `None`, that rule is neglected but `False` will prevent to get tweets that contains that rule.

Each tweet is send to telegram endpoint as telegram message. In the end of each message, the Author's name(or account's name) is aaded in the format of `-Author name-`. You can change the representation of Author name by defining appropriate prefix and suffix:
```
AUTHOR_PREFIX = '-'

AUTHOR_SUFFIX = '-'
```

### Commands
Available commands are as below:
```
python3 main.py --main/-M                                 # will start to get real-time tweets
python3 main.py --get-rules/-G                            # will shows the ids of existing rules
python3 main.py --add-rules/-A username [username ...]    # will get tweets from provided usernames
python3 main.py --del-rules/-D rule_id [rule_id ...]      # will delete provided rules from twitter
```

Before start to streaming tweets You should add some username to get tweets from. For example:
```
python3 main.py --add-rules foo bar baz
```
This command by default will set below rule to twitter:
```
(from:foo) OR (from:bar) OR (from:baz) -is:retweet -is:reply -is:quote
```
And finally you can run `python3 main.py --main` to start streaming


# TODO
- Adding file store backend
- Distingush quotes, replies and retweets in telegram by reply to source message
