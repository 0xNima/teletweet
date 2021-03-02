class Logger:
    import logging
    from logging.handlers import RotatingFileHandler

    def __init__(self, **kwargs):
        self.logger = Logger.logging.getLogger('root')
        self.logger.setLevel(Logger.logging.INFO)
        __formatter = Logger.logging.Formatter("%(name)s %(asctime)s [%(levelname)s] %(message)s")
        __handlers = []
        if kwargs.get("file_name"):
            __handlers.append(
                Logger.RotatingFileHandler(filename=kwargs.get("file_name"), mode='a', maxBytes=5 * 1024 * 1024,
                                           backupCount=10))
        if kwargs.get("enable_stream"):
            __handlers.append(Logger.logging.StreamHandler())

        for handler in __handlers:
            handler.setLevel(Logger.logging.INFO)
            handler.setFormatter(__formatter)
            self.logger.addHandler(handler)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def warn(self, msg):
        self.logger.warning(msg)
