from overlay_north.provider_db import ProviderDb
import os
import json


class Startup:
    def __init__(self):
        self.provider_db = ProviderDb()

    def start(self):
        if self.provider_db.create_tables():
            return True
        else:
            return False
