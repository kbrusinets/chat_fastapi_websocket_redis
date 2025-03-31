from services.db import Db


class ModuleWithDb:
    def __init__(self, db : Db):
        self.db = db
