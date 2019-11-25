import commands.standard


class CommandManager:

    commands = {}

    def __init__(self):
        commands_list = list()
        commands_list.append(commands.standard.Greeting())
        commands_list.append(commands.standard.Compress())
        help_command = commands.standard.Help()
        commands_list.append(help_command)
        for command in commands_list:
            self.__add_command(command)
        help_command.commands_dict = self.commands
        help_command.commands_list = commands_list

    def __add_command(self, command):
        for name in command.variants:
            self.commands[name] = command
