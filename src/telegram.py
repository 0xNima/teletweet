import json

from src import requests, logger, TELEGRAM_BOT_URL, TARGET_TELEGRAM_ENDPOINT, PATH
from src.helpers import get_video_url
from src.tweet import Tweet


class InputMedia:
    @classmethod
    def get_instance(cls, **kwargs):
        return {"type": kwargs.get("type"),
                "media": kwargs.get("preview_image_url") if kwargs.get("preview_image_url") else kwargs.get("url"),
                "caption": kwargs.get("caption", ""),
                "parse_mode": "HTML"}


class InputMediaPhoto(InputMedia):
    @classmethod
    def get_instance(cls, **kwargs):
        return super().get_instance(**kwargs)


class InputMediaVideo(InputMedia):
    @classmethod
    def get_instance(cls, **kwargs):
        result = super().get_instance(**kwargs)
        video_info = kwargs.get("video_info")
        result.update({"media": get_video_url(video_info.get("variants")) if video_info else kwargs.get(
            "preview_image_url"),
                       "duration": video_info.get("duration_millis") if video_info else kwargs.get("duration_ms"),
                       "thumb": kwargs.get("media_url") if not video_info else kwargs.get("preview_image_url"),
                       "with": kwargs.get("width") if not video_info else None,
                       "height": kwargs.get("height") if not video_info else None})
        return result


class TelegramMediaProxy:

    @staticmethod
    def __tg_send_message(**kwargs):
        url = TELEGRAM_BOT_URL.format("sendMessage")
        response = requests.post(url=url, data={
            "chat_id": TARGET_TELEGRAM_ENDPOINT,
            "text": kwargs.get("text"),
            "parse_mode": "html",
            "disable_web_page_preview": kwargs.get("disable_web_page_preview", True),
        })
        return response

    @staticmethod
    def __tg_send_photo(**kwargs):
        url = TELEGRAM_BOT_URL.format("sendPhoto")
        response = requests.post(url=url, data={
            "chat_id": TARGET_TELEGRAM_ENDPOINT,
            "photo": kwargs.get("url"),
            "caption": kwargs.get("caption"),
            "parse_mode": "HTML",
        })
        return response

    @staticmethod
    def __tg_send_group_media(media_list):
        url = TELEGRAM_BOT_URL.format("sendMediaGroup")
        input_media = []
        for media in media_list:
            if media.get("type") == "photo":
                _m = InputMediaPhoto.get_instance(**media)
            else:
                _m = InputMediaVideo.get_instance(**media)
            input_media.append(_m)

        response = requests.post(url=url, data={
            "chat_id": TARGET_TELEGRAM_ENDPOINT,
            "media": json.dumps(input_media),
        })
        return response

    @staticmethod
    def __tg_send_video(**kwargs):
        _type = kwargs.get("type", "video")
        url = TELEGRAM_BOT_URL.format(PATH.get(_type))
        video_info = kwargs.get("video_info")
        response = requests.post(url=url, data={
            "chat_id": TARGET_TELEGRAM_ENDPOINT,
            "caption": kwargs.get("caption"),
            "parse_mode": "HTML",
            _type: get_video_url(video_info.get("variants")) if video_info else kwargs.get("preview_image_url"),
            "duration": video_info.get("duration_millis") if video_info else kwargs.get("duration_ms"),
            "thumb": kwargs.get("media_url") if not video_info else kwargs.get("preview_image_url"),
            "with": kwargs.get("width") if not video_info else None,
            "height": kwargs.get("height") if not video_info else None,
        })
        return response

    @classmethod
    def send_media(cls, media, media_obj):
        try:
            if media == "animated_gif":
                media = "video"
                media_obj.update({"type": "animation"})
            func = getattr(cls, "_TelegramMediaProxy__tg_send_{}".format(media))
            if media == "group_media":
                tg_response = func(media_obj)
            else:
                tg_response = func(**media_obj)
            if tg_response.status_code >= 500:
                raise Exception(
                    "telegram failed request: {}\n\t\t{}".format(tg_response.status_code, tg_response.json()))
        except Exception as ex:
            raise Exception("send_media failed {}".format(ex))


def send(tweet_json):
    try:
        tweet = Tweet(tweet_json)
        if tweet.media is not None:
            if len(tweet.media) == 1:
                media_obj = tweet.media[0]
                media_obj.update({"caption": tweet.text})
                return TelegramMediaProxy.send_media(media_obj.get("type"), media_obj)
            elif len(tweet.media) > 1:
                tweet.media[0].update({"caption": tweet.text})
                TelegramMediaProxy.send_media("group_media", tweet.media)
        else:
            TelegramMediaProxy.send_media("message", {"text": tweet.text})
    except Exception as e:
        logger.error("can't send tweet to telegram error: \n\t{}".format(e))
