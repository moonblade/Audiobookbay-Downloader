import logging

def custom_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set your desired logging level

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"  # Customize date format as needed
    )

    handler = logging.StreamHandler()  # Or a FileHandler if you want to write to a file
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
