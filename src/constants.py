from .config import *

TWITTER_RULES_URL = "https://api.twitter.com/2/tweets/search/stream/rules"

HEADERS = {"Content-type": "application/json", "Authorization": "Bearer {}".format(TWITTER_BEARER_TOKEN)}

TWITTER_STREAM_URL = "https://api.twitter.com/2/tweets/search/stream"

TWITTER_MEDIA_URL = "https://api.twitter.com/2/tweets?ids={}&expansions=attachments.media_keys, author_id&media.fields=" \
                    "duration_ms,height,media_key,preview_image_url,public_metrics,type,url,width"

TELEGRAM_BOT_URL = "https://api.telegram.org/bot%s/{}" % TELEGRAM_BOT_TOKEN


TWITTER_STATUS_URL = "https://api.twitter.com/1.1/statuses/show.json?id={}&extended_entities=true&tweet_mode=extended"

PATH = {
    "video": "sendVideo",
    "animation": "sendAnimation"
}

TWITTER_RULE_LIMIT = 25     # don't change this unless with enterprise or premium api keys

TWITTER_PER_RULE_CHAR_LIMIT = 512     # don't change this unless with enterprise or premium api keys

RETRY_DELAY = 10    # in seconds
