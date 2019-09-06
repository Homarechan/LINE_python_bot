import sys
import os
import linepy
import mysql.connector
from akad import ttypes

import runner
import error_handler


class MainCls:
    def __init__(self):
        authtoken = os.getenv("AUTH_TOKEN")
        if not (authtoken):
            sys.stderr.write("$AUTH_TOKEN must be set")
            sys.exit(1)
        self.cl = linepy.LINE(idOrAuthToken=authtoken)
        self.oepoll = linepy.OEPoll(self.cl)

        mysql_user_name = os.getenv("MYSQL_USER_NAME")
        mysql_password = os.getenv("MYSQL_PASSWORD")
        self.conn = mysql.connector.connect(
            user=mysql_user_name,
            password=mysql_password,
            host="localhost",
            database="linedatas",
        )
        self.cur = self.conn.cursor()

        self.runner = runner.Runner(self)
        self.error_handler = error_handler.ErrorHandler(self)

        self.logfile = open("./log/log.txt", "w")

    def __del__(self):
        try:
            self.cur.close()
            self.conn.close()
            self.logfile.close()
        except:
            pass

    def run_main(self):
        while 1:
            try:
                operations = self.oepoll.singleTrace()
                if operations is not None:
                    for operation in operations:
                        self.runner.parse_and_run(operation)
                        self.oepoll.setRevision(operation.revision)
            except Exception as e:
                self.error_handler.output_error(self.logfile, e)


if __name__ == "__main__":
    Main: MainCls = MainCls()
    Main.run_main()
