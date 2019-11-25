import commands.command as command
import os
import os.path
import requests
from pyunpack import Archive
import json
from PIL import Image


COMMAND_PREFIX = "!"


class Greeting(command.Command):

    variants = ["hi", "hello"]
    args = []
    description = "Bot says you \"Hi!\""

    def execute(self, payload):
        data = payload["data"]
        web_client = payload["web_client"]
        channel_id = data["channel"]
        user = data["user"]
        web_client.chat_postMessage(
            channel=channel_id,
            text=f"Hi, <@{user}>!",
        )


class Compress(command.Command):

    STORAGE_PATH = "temp/"
    CONFIG_NAME = "/config.json"
    IMAGE_NAMES = ("/image.png", "/image.jpg")

    variants = ["comp", "compress"]
    args = []
    description = "Bot compress image by specified configuration. With this command you must send:\n" \
                  "\t* config.json file with JSON that contains following fields:\n" \
                  "\t\t- size_x - specify width of image\n" \
                  "\t\t- size_y - specify height of image\n" \
                  "\t\t- black_white(optional) - specify should bot make image black and white or not\n" \
                  "\t* image.png / image.jpg - specify image that bot should compress\n"

    def execute(self, payload):
        data = payload["data"]
        channel_id = data["channel"]
        web_client = payload["web_client"]

        try:
            file_url = data["files"][0]["url_private_download"]
        except KeyError:
            web_client.chat_postMessage(channel=channel_id, text="You must send archive with this command")
            return

        file_path = Compress.STORAGE_PATH + data["files"][0]["id"]
        file_name = file_path + "/" + data["files"][0]["name"]
        token = os.environ["SLACK_SAMPLE_BOT_TOKEN"]
        response = requests.get(file_url, headers={"Authorization": "Bearer " + token})
        if response.status_code == 200:
            os.mkdir(file_path)
            open(file_name, "wb").write(response.content)

            try:
                Archive(file_name).extractall(file_path)
            except Exception:
                web_client.chat_postMessage(channel=channel_id, text="Could not open archive")
                return

            try:
                config = Compress.parse_config(file_path + Compress.CONFIG_NAME)
            except ConfigParseError as e:
                web_client.chat_postMessage(channel=channel_id, text=e.args[0])
                return

            try:
                for image_name in Compress.IMAGE_NAMES:
                    if os.path.exists(file_path + image_name):
                        Compress.compress_image(file_path + image_name, config)
                        web_client.files_upload(channels=channel_id, file=file_path + image_name)
                        break
                else:
                    web_client.chat_postMessage(channel=channel_id, text="Archive must contain image.png or image.jpg file")
            except ConfigParseError:
                web_client.chat_postMessage(channel=channel_id, text="Could not compress image")

        else:
            web_client.chat_postMessage(channel=channel_id, text="Could not download file")

    @staticmethod
    def parse_config(config_path):
        try:
            with open(config_path) as config:
                config_data = json.load(config)
        except FileNotFoundError as e:
            raise ConfigParseError("Archive must contain config.json file with compressing configuration") from e
        except json.decoder.JSONDecodeError:
            raise ConfigParseError("Config.json must contains valid JSON")

        try:
            width = int(config_data["size_x"])
        except ValueError as e:
            raise ConfigParseError("Field \"size_x\" must be an integer") from e
        except KeyError as e:
            raise ConfigParseError("Config must contain \"size_x\" field") from e

        try:
            height = int(config_data["size_y"])
        except ValueError as e:
            raise ConfigParseError("Field \"size_y\" must be an integer") from e
        except KeyError as e:
            raise ConfigParseError("Config must contain \"size_y\" field") from e

        try:
            make_bw = bool(config_data["black_white"])
        except ValueError as e:
            raise ConfigParseError("Field \"size_y\" must be an boolean") from e
        except KeyError:
            make_bw = False

        return {"width": width, "height": height, "make_bw": make_bw}

    @staticmethod
    def compress_image(image_path, config):
        image = Image.open(image_path)
        resized_image = image.resize((config["width"], config["height"]), Image.ANTIALIAS)
        if config["make_bw"]:
            resized_image = resized_image.convert("L")
        resized_image.save(image_path)


class Help(command.Command):

    commands_dict = None
    commands_list = None

    variants = ["help"]
    args = ["<command_name>"]
    description = "Bot writes description for specified command"

    def execute(self, payload):
        data = payload["data"]
        channel_id = data["channel"]
        web_client = payload["web_client"]
        try:
            command_name = data["text"].split(" ", maxsplit=1)[1]
        except IndexError:
            text_parts = list()
            for current_command in self.commands_list:
                text_parts.append(Help.__build_command_description(current_command, True))
            web_client.chat_postMessage(channel=channel_id, text="".join(text_parts))
            return
        try:
            text = Help.build_command_description(self.commands_dict[command_name], False)
            web_client.chat_postMessage(channel=channel_id, text=text)
        except KeyError:
            web_client.chat_postMessage(channel=channel_id, text="Unknown command. Use help command without args")

    @staticmethod
    def build_command_description(current_command, append_new_line):
        message_parts = list()
        message_parts.extend(" / ".join(list(map(Help.__add_prefix, current_command.variants))))
        if current_command.args:
            message_parts.append(" (args: ")
            message_parts.extend(current_command.args)
            message_parts.append(")")
        message_parts.append(" - ")
        message_parts.extend(current_command.description)
        if append_new_line:
            message_parts.append("\n")
        return "".join(message_parts)

    @staticmethod
    def __add_prefix(x):
        return COMMAND_PREFIX + x


class ConfigParseError(Exception):
    pass
