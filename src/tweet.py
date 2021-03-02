from src import re, requests, redis_cli, logger, TWITTER_BEARER_TOKEN, TWITTER_STATUS_URL, AUTHOR_PREFIX, AUTHOR_SUFFIX


class Tweet:
    def __init__(self, raw_tweet: dict):
        self.includes = raw_tweet.get("includes")
        self.raw_tweet = raw_tweet.get("data")
        self.tweet_id = self.raw_tweet.get("id")
        self.author_id = self.raw_tweet.get("author_id")
        self.media = self.includes.get("media")
        self.user = self.includes.get("users")[0]
        self.username = self.user.get("username")
        self.account_name = self.user.get("name")
        self.text = self.raw_tweet.get("text")
        self.created_at = self.raw_tweet.get("created_at")
        self.__parse_text()
        self.__change_mention_url()
        self.__process_media()
        self.__add_account_to_text()
        redis_cli.hsetnx("twitter_accounts", self.username, "{}@{}".format(self.author_id, self.account_name))

    def __add_account_to_text(self):
        self.text = "{}\n\n{}{}{}".format(self.text, AUTHOR_PREFIX, self.account_name, AUTHOR_SUFFIX)

    def __parse_text(self):
        self.text = re.sub(r'https://t.co/\w+\b', "", self.text)

    def __change_mention_url(self):
        mentions = re.findall(r'@\w+\b', self.text)
        for mention in mentions:
            self.text = self.text.replace(
                mention, "<a href='https://twitter.com/{}'>{}</a>".format(mention, mention.replace("@", "")))

    def __process_media(self):
        if self.media:
            if self.media[0].get("type") in ["video", "animated_gif"]:
                self.__get_video_from_v1()

    def __get_video_from_v1(self):
        tweet_status = requests.get(TWITTER_STATUS_URL.format(self.tweet_id),
                                    headers={"Authorization": "Bearer {}".format(TWITTER_BEARER_TOKEN)})
        if tweet_status.status_code == 200:
            extended_entities = tweet_status.json().get("extended_entities")
            if extended_entities:
                self.media = extended_entities.get("media")
            else:
                logger.error("can't get extended_entities details: \n\t{}".format(tweet_status.json()))
