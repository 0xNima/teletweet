from src.constants import *
from src.log import Logger
import redis
import re
import requests
import argparse

pool = redis.ConnectionPool(**REDIS_BACKEND_CONFIG)

redis_cli = redis.Redis(connection_pool=pool)

log_options = {}

if FILE_LOGGING_ENABLE:
    log_options['file_name'] = LOG_FILE

log_options['enable_stream'] = CONSOLE_LOGGING_ENABLE

logger = Logger(**log_options)

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--main', '-M', help='start streaming twits and send them to telegram endpoint', action='store_true')
group.add_argument('--del-rules', '-D', help='delete specified rules', nargs='+', metavar='rule_id')
group.add_argument('--add-rules', '-A', help='add specified rules', nargs='+', metavar='username')
group.add_argument('--get-rules', '-G', help='get all rules', action='store_true')

ADDITIONAL_RULES = str()

if MANUAL_RULE:
    ADDITIONAL_RULES = MANUAL_RULE
else:
    names = {0: 'is:quote ', 1: 'is:reply ', 2: 'is:retweet ', 3: 'is:verified'}
    for index, rule in enumerate([GET_QUOTE_TWEETS, GET_REPLY_TWEETS, GET_RETWEET_TWEETS, GET_VERIFIED_TWEETS]):
        if rule is not None:
            if rule:
                ADDITIONAL_RULES += names.get(index)
            else:
                ADDITIONAL_RULES += "-{}".format(names.get(index))
