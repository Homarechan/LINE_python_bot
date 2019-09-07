from akad import ttypes
import subprocess
import main
import os
import re

import parser


class Runner:
    def __init__(self, main_instance):
        self.main_instance = main_instance
        self.parser = parser.Parser(main_instance)

        self.may_be_sql_injection = re.compile(r"[o|O][r|R]")

        self.compile_language = ["C", "C++", "HASKELL", "GO", "V", "NIM"]
        self.script_language = [
            "PYTHON",
            "PYTHON3",
            "PYTHON2",
            "RUBY",
            "CLISP",
            "JULIA",
            "JAVA",
        ]

    def parse_and_run(self, operation: ttypes.Operation):
        operation_type: ttypes.OpType = operation.type

        if operation_type == ttypes.OpType.NOTIFIED_ADD_CONTACT:
            self.main_instance.cur.execute(
                'SELECT switch FROM setting WHERE name="auto_add"'
            )

            if self.main_instance.cur.fetchall()[0][0]:
                self.main_instance.cur.execute(
                    'SELECT contents FROM greeting WHERE name="auto_add"'
                )
                string = self.parser.parse_add_friend(
                    self.main_instance.cur.fetchall()[0][0], operation
                )
                self.main_instance.cl.sendMessage(operation.param1, string)

        if operation_type == ttypes.OpType.NOTIFIED_INVITE_INTO_GROUP:
            if self.main_instance.cl.mid in operation.param2:
                self.main_instance.cur.execute(
                    'SELECT switch FROM setting WHERE name="auto_join"'
                )

                if self.main_instance.cur.fetchall()[0][0]:
                    self.main_instance.cl.acceptGroupInvitation(operation.param1)
                    self.main_instance.cur.execute(
                        'SELECT contents FROM greeting WHERE name="auto_join"'
                    )
                    string = self.parser.parse_join_group(
                        self.main_instance.cur.fetchall()[0][0], operation
                    )
                    self.main_instance.cl.sendMessage(operation.param1, string)

        if operation_type == ttypes.OpType.RECEIVE_MESSAGE:
            message = operation.message
            if message.text == None:
                return
            
            sendto = message._from if message.totype == ttypes.MIDType.USER else message.to

            if message.text.startswith("setting"):
                self.main_instance.cur.execute("SELECT mid FROM admin")

                if message._from in [n[0] for n in self.main_instance.cur.fetchall()]:
                    if self.may_be_sql_injection.search(message.text):
                        self.main_instance.cl.sendMessage(sendto, "不正な文字列です")
                    else:
                        cmd: list = message.text.split(":")

                        self.main_instance.cur.execute(
                            f'SELECT switch FROM setting WHERE name="{cmd[1]}"'
                        )
                        result = self.main_instance.cur.fetchall()

                        if len(result):
                            switch = bool(result[0][0])
                            switch_input = cmd[2] in ["on", "ON"]

                            if switch == switch_input:
                                self.main_instance.cl.sendMessage(
                                    sendto,
                                    f'{cmd[1]}はすでに{"オン" if switch_input else "オフ"}です',
                                )
                            else:
                                self.main_instance.cur.execute(
                                    f'UPDATE setting SET switch={"true" if switch_input else "false"} WHERE name="{cmd[1]}"'
                                )
                                self.main_instance.cl.sendMessage(
                                    sendto,
                                    f'{cmd[1]}を{"オン" if switch_input else "オフ"}にしました',
                                )
                        else:
                            self.main_instance.cl.sendMessage(sendto, "不明な設定です")
                else:
                    # self.main_instance.cl.sendMessage(sendto, "")
                    pass

            elif message.text.startswith("setgreeting"):
                self.main_instance.cur.execute("SELECT mid FROM admin")

                if message._from in [n[0] for n in self.main_instance.cur.fetchall()]:
                    if self.may_be_sql_injection.search(message.text):
                        self.main_instance.cl.sendMessage(sendto, "不正な文字列です")
                    else:
                        cmd: list = message.text.split(":")
                        cmd[2] = ":".join(cmd[2:])

                        self.main_instance.cur.execute(
                            f'SELECT contents FROM greeting WHERE name="{cmd[1]}"'
                        )
                        result = self.main_instance.cur.fetchall()

                        if len(result):
                            self.main_instance.cur.execute(
                                f'UPDATE greeting SET contents="{cmd[2]}" WHERE name="{cmd[1]}"'
                            )
                            self.main_instance.cl.sendMessage(
                                sendto, f"{cmd[1]}\nのメッセージを\n{cmd[2]}\nに変更しました"
                            )
                        else:
                            self.main_instance.cl.sendMessage(sendto, "不明なコマンドです")
                else:
                    # self.main_instance.cl.sendMessage(sendto, "")
                    pass

            elif message.text.startswith("add_admin"):
                if message._from == "uc48345d5b2cb32aec49843f009caa5cc":
                    mid = message.text.split(":")[1]
                    self.main_instance.cur.execute(f'INSERT INTO admin VALUES("{mid}")')
                    contact = self.main_instance.cl.getContact(mid)
                    self.main_instance.cl.sendMessage(
                        sendto, f"{contact.displayName}を権限者に追加しました"
                    )

            elif message.text == "info":
                _text = ""
                self.main_instance.cur.execute("SELECT * FROM setting")

                result = []
                for setting in self.main_instance.cur.fetchall():
                    result.append(list(map(str, setting)))

                for setting in result:
                    _text += ":".join(setting)
                    _text += "\n"

                self.main_instance.cl.sendMessage(sendto, _text.strip())

            elif message.text.startswith("--run"):
                self.main_instance.cur.execute("SELECT mid FROM admin")

                if message._from in [n[0] for n in self.main_instance.cur.fetchall()]:
                    tokens = message.text.split("\n")
                    cmd = tokens[0].split()
                    src = "\n".join(tokens[1:])

                    lang = cmd[1].upper()
                    options = cmd[2:]

                    named = []

                    if lang in self.compile_language:
                        if lang == "C":
                            compiler = ["gcc"]
                            suffix = "c"
                            named = ["-o", "temp"]
                            remove = ["temp.c", "temp"]

                        elif lang == "C++":
                            compiler = ["g++"]
                            suffix = "cpp"
                            named = ["-o", "temp"]
                            remove = ["temp.cpp", "temp"]

                        elif lang == "HASKELL":
                            compiler = ["ghc"]
                            suffix = "hs"
                            named = []
                            remove = ["temp.hs", "temp.hi", "temp.o", "temp"]

                        elif lang == "GO":
                            compiler = ["go", "build"]
                            suffix = "go"
                            named = []
                            remove = ["temp.go", "temp"]

                        elif lang == "V":
                            compiler = ["v"]
                            suffix = "v"
                            named = []
                            remove = ["temp.v", "temp"]

                        elif lang == "NIM":
                            compiler = ["nim", "c"]
                            suffix = "nim"
                            named = []
                            remove = ["temp.nim", "temp"]

                        filename = "temp." + suffix

                        with open(filename, "w") as fp:
                            fp.write(src)

                        command = compiler + [filename] + named + options

                        try:
                            with open("error.txt", "w") as fp:
                                subprocess.check_call(command, stderr=fp)
                        except subprocess.CalledProcessError:
                            with open("error.txt", "r") as fp:
                                self.main_instance.cl.sendMessage(
                                    sendto, fp.read().strip()
                                )
                            subprocess.check_call(["rm", filename])
                            return

                        try:
                            with open("error.txt", "w") as fp:
                                result = subprocess.check_output("./temp", stderr=fp)
                                self.main_instance.cl.sendMessage(
                                    sendto, result.decode().strip()
                                )

                        except subprocess.CalledProcessError:
                            with open("error.txt", "r") as fp:
                                self.main_instance.cl.sendMessage(
                                    sendto, fp.read().strip()
                                )

                        finally:
                            subprocess.check_call(["rm"] + remove)

                    elif lang in self.script_language:
                        if lang == "PYTHON" or lang == "PYTHON3":
                            interpreter = ["python"]
                            suffix = "py"
                        elif lang == "PYTHON2":
                            interpreter = ["python2"]
                            suffix = "py"
                        elif lang == "RUBY":
                            interpreter = ["ruby"]
                            suffix = "rb"
                        elif lang == "CLISP":
                            interpreter = ["sbcl", "--script"]
                            suffix = "cl"
                        elif lang == "JULIA":
                            interpreter = ["julia"]
                            suffix = "jl"
                        elif lang == "JAVA":
                            interpreter = ["java"]
                            suffix = "java"

                        filename = "temp." + suffix

                        with open(filename, "w") as fp:
                            fp.write(src)

                        try:
                            with open("error.txt", "w") as fp:
                                result = subprocess.check_output(
                                    interpreter + [filename], stderr=fp
                                )
                                self.main_instance.cl.sendMessage(
                                    sendto, result.decode().strip()
                                )

                        except subprocess.CalledProcessError:
                            with open("error.txt", "r") as fp:
                                self.main_instance.cl.sendMessage(
                                    sendto, fp.read().strip()
                                )

                        finally:
                            subprocess.check_call(["rm", filename])
