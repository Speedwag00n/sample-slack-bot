import commands.standard


class CommandHandler:

    commands = {}

    def __init__(self):
        print()
        self.__add_command(commands.standard.Greeting())

    def __add_command(self, command):
        for name in command.variants:
            self.commands[name] = command