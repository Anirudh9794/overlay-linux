import json
import subprocess
from overlay_north.provider_db import ProviderDb


class ConfigHandler:

    def __init__(self):
        self.db = ProviderDb()

    def clean_start(self):
        output = {}
        clean_start = args["cleanStart"]

        print("inside clean start")

        # run all delete ansiblee scripts
        phy_result = self.clean_physically()

        # on script success...restart the db tables
        if phy_result["success"] == True:
            db_result = self.clean_db()

            if db_result["success"] == True:
                output["success"] = True
            else:
                output["success"] = False
                output["notice"] = db_result
        else:
            output["success"] = False
            output["notice"] = phy_result

    def clean_physically(self):
        result = {}
        result["success"] = True  # TODO: Fix this!

        print("Inside clean physically")

        return result

    def clean_db(self):
        result["success"] = False
        if self.db.delete_all_tables():
            create_ok = self.db.create_tables()

            if create_ok:
                result["message"] = "Succesfully deleted all tables and re-created them"
                result["success"] = True
            else:
                result["message"] = "Succesfully deleted all tables but failed to re-create them"
                result["success"] = False
        else:
            result["message"] = "Failed to delete all tables"
            result["success"] = False

        return result
