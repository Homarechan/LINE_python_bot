import main
from akad import ttypes


class Parser:
    def __init__(self, main_instance):
        self.main_instance = main_instance

    def parse_add_friend(self, string: str, operation: ttypes.Operation):
        if "%1" in string:
            contact = self.main_instance.cl.getContact(operation.param1)
            string = string.replace("%1", contact.displayName)
        return string

    def parse_join_group(self, string: str, operation: ttypes.Operation):
        if "%1" in string:
            group = self.main_instance.cl.getGroup(operation.param1)
            string = string.replace("%1", group.name)
        if "%2" in string:
            contact = self.main_instance.cl.getContact(operation.param2)
            string = string.replace("%2", contact.displayName)
        return string
