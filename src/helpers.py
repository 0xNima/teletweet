import json

from src import re, requests, redis_cli, logger, TWITTER_RULES_URL, HEADERS, TWITTER_RULE_LIMIT, \
    TWITTER_PER_RULE_CHAR_LIMIT, TWITTER_STREAM_URL, TWITTER_BEARER_TOKEN, ADDITIONAL_RULES


def police(suspect):
    def judge(*args, **kwargs):
        try:
            return suspect(*args, **kwargs)
        except Exception as crime:
            logger.error("an error occurred while calling {} function - detail: \n\t{}".format(suspect.__name__, crime))
            return 500
    return judge


@police
def get_twitter_rules(save=True):
    response = requests.get(url=TWITTER_RULES_URL, headers=HEADERS)
    if response.status_code == 200:
        rules = response.json()
        if save:
            for rule in rules.get("data"):
                redis_cli.hsetnx("rules", rule.get("id"), rule.get("value"))
        return rules
    return response.json()


@police
def __add_twitter_rules(rule_raw_value):
    response = requests.post(
        url=TWITTER_RULES_URL,
        headers=HEADERS,
        json={"add": [
            {"value": rule_raw_value}
        ]}
    )
    return response


def __store_to_redis(rules_raw_text, rule_id):
    redis_cli.hset('rules', rule_id, rules_raw_text)
    parsed_rules = list(map(lambda x: x.replace('from:', ''), re.findall(r'from:\w+\b', rules_raw_text)))
    for rule in parsed_rules:
        redis_cli.hset('username_rid', rule, rule_id)


@police
def __set_multiple_rules(multiple_rule):
    response = __add_twitter_rules(multiple_rule)
    if response.status_code == 201:
        data = response.json().get("data")[0]
        __store_to_redis(multiple_rule, data.get("id"))
        logger.info("set multiple rule successfully")
        return 200

    logger.error("failed to set multiple rule: {} \n\t {}".format(response.status_code, response.json()))
    return 500


@police
def set_rule(username):
    if not redis_cli.hexists("username_rid", username):
        rule = "from:{}".format(username)
        ids = redis_cli.hkeys('rules')
        old_rid = None
        new_value = "({}) {}".format(rule, ADDITIONAL_RULES)
        for i, id_ in enumerate(ids):
            id_ = id_.decode()
            new_value = redis_cli.hget('rules', id_).decode().replace('(', '({} OR '.format(rule))
            if len(new_value) <= TWITTER_PER_RULE_CHAR_LIMIT:
                old_rid = id_
                logger.info("new rule setup for {} - replace to rid: {}".format(username, id_))
                break
            else:
                if i == TWITTER_RULE_LIMIT - 1:
                    logger.info("{} rules limit exceeded. Failed to add {}".format(TWITTER_RULE_LIMIT, username, id_))
                    return -2, '{} rules limit exceeded'.format(TWITTER_RULE_LIMIT)
                if i == len(ids) - 1:
                    new_value = "({}) {}".format(rule, ADDITIONAL_RULES)
                    logger.info("new rule setup for {}. create new rid".format(username))
                else:
                    continue
        response = __add_twitter_rules(new_value)
        data = None
        if response.status_code == 201:
            if old_rid and delete_rule_by_id([old_rid]) != 200:
                logger.error('can\'t delete previous rule with rid: {}'.format(old_rid))
                redis_cli.hset('garbage', old_rid, 1)
            if old_rid:
                redis_cli.hdel('rules', old_rid)
            data = response.json().get("data")[0]
            rid = data.get("id")
            __store_to_redis(new_value, rid)
        else:
            logger.error("{}: {}".format(response.status_code, response.json()))
        return response.status_code, data
    else:
        return -1, "username already exist"


def delete_rule_by_username(username):
    rid = redis_cli.hget('username_rid', username)
    if rid:
        rid = rid.decode()
        new_rule = redis_cli.hget('rules', rid).decode().replace("from:{}".format(username), '') \
            .replace('( OR ', '(').replace(' OR )', ')').replace(' OR  OR ', ' OR ')

        if new_rule.find("from") == -1:
            logger.info("the rule is empty. nothing to do")
            if delete_rule_by_id([rid]) == 200:
                return 200
            logger.error('can\'t delete previous rule with rid: {} - saved rid to garbage'.format(rid))
            return 500
        res = __set_multiple_rules(new_rule)
        if res == 200:
            if delete_rule_by_id([rid]) != 200:
                logger.error('can\'t delete rid: {} - saved to garbage'.format(rid))
            return 200
        return res
    return 404


@police
def delete_rule_by_id(ids, delete_all=False, delete_related_usernames=True):
    if not ids:
        ids = list(map(lambda x: x.decode(), redis_cli.hkeys('rules')))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        TWITTER_RULES_URL,
        headers=HEADERS,
        json=payload
    )
    if response.status_code == 200:
        if delete_all:
            redis_cli.delete('rules')
            redis_cli.delete('username_rid')
        else:
            for rid in ids:
                rule = redis_cli.hget('rules', rid)
                if delete_related_usernames:
                    parsed_rules = list(map(lambda x: x.replace('from:', ''), re.findall(r'from:\w+\b', rule.decode())))
                    for rule in parsed_rules:
                        redis_cli.hdel('username_rid', rule)
                    redis_cli.hdel("rules", rid)
        logger.info("delete rules from twitter successfully")
        return 200
    [redis_cli.hset('garbage', rid, 1) for rid in ids]
    logger.error("delete rules from twitter failed: {} \n\t {}".format(response.status_code, response.json()))
    return response.status_code


def get_rules_from_cache():
    return redis_cli.hlen("rules")


def get_video_url(variants):
    N = {'bitrate': 0}
    for v in variants:
        br = v.get("bitrate")
        if br is not None and br >= N.get("bitrate"):
            N = v
    return N.get("url")


@police
def get_stream():
    from src.telegram import send
    with requests.get(
            TWITTER_STREAM_URL, headers={"Authorization": "Bearer {}".format(TWITTER_BEARER_TOKEN)}, stream=True,
            params={
                "tweet.fields": "attachments,author_id,created_at,source",
                "expansions": "author_id,attachments.media_keys",
                "media.fields": "duration_ms,height,media_key,preview_image_url,type,url,width"
            }
    ) as response:
        logger.info("stream status code: {}".format(response.status_code))
        if response.status_code != 200:
            raise Exception(
                "Cannot get stream (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )
        for response_line in response.iter_lines():
            if response_line:
                json_response = json.loads(response_line)
                if json_response.get("includes"):
                    logger.info("get new tweet from: {}".format(json_response.get("includes").get('users')))
                if json_response.get("error"):
                    raise Exception("Disconnected")
                send(json_response)
