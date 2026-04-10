import os

class Config:
    """Application env config"""
    def __init__(self):
        self.TOKEN = os.environ.get('TG_TOKEN')
        self.PROXY_URL = os.environ.get('PROXY_URL')
        DB_RELEASE_PATH = '/var/lib/kefirchik/kefirchik.db'
        DB_DEBUG_PATH = '../Database/kefirchik.db'
        # default local run
        self.USE_WEB_HOOKS = False
        self.DB_PATH = DB_DEBUG_PATH
        self.IS_PROD = False
        MODE = os.environ.get('MODE')
        if MODE == 'release':
            self.USE_WEB_HOOKS = True
            self.IS_PROD = True
            self.DB_PATH = DB_RELEASE_PATH
        elif MODE == 'release-pooling':
            self.USE_WEB_HOOKS = False
            self.IS_PROD = True
            self.DB_PATH = DB_RELEASE_PATH
        elif MODE == 'debug':
            self.USE_WEB_HOOKS = False
            self.DB_PATH = DB_RELEASE_PATH
