import time

from src import logger, RETRY_DELAY, parser
from src.helpers import get_rules_from_cache, set_rule, get_twitter_rules, delete_rule_by_id, get_stream

if __name__ == '__main__':
    args = parser.parse_args()
    if args.main:
        rules = get_rules_from_cache()
        if not rules:
            logger.error("There is no rule, First define the rules \n")
        logger.info("Start to Streaming")
        while True:
            try:
                get_stream()
            except Exception as e:
                logger.error("an error is occurred: {}\n retry after {} seconds".format(e, RETRY_DELAY))
                time.sleep(RETRY_DELAY)
    if args.add_rules:
        for username in args.add_rules:
            if username:
                if username.startswith('@'):
                    username = username.replace('@', '', 1)
                set_rule(username)
    elif args.del_rules:
        if args.del_rules[0] == 'all':
            delete_rule_by_id([], delete_all=True)
        else:
            for rule in args.del_rules:
                delete_rule_by_id([rule])
    elif args.get_rules:
        rules = get_twitter_rules(save=False)
        logger.info(rules)
