import traceback
import main
import sys
import _io


class ErrorHandler:
    def __init__(self, main_instance):
        ...

    def output_error(self, stream: _io.TextIOWrapper, error: Exception):
        for arg in error.args:
            stream.write(str(arg))
            stream.write("\n")
