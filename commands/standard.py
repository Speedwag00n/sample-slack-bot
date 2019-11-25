import commands.command as command
import os
import os.path
import requests
from pyunpack import Archive
import json
from PIL import Image


class Greeting(command.Command):

    variants = ["hi", "hello"]

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

    def execute(self, payload):
        data = payload["data"]
        channel_id = data["channel"]
        web_client = payload["web_client"]

        try:
            file_url = data["files"][0]["url_private_download"]
        except KeyError:
            web_client.chat_postMessage(channel=channel_id, text="You must send archive with this command")
            return

        file_path = self.STORAGE_PATH + data["files"][0]["id"]
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
                config = self.__parse_config(file_path + self.CONFIG_NAME)
            except ConfigParseError as e:
                web_client.chat_postMessage(channel=channel_id, text=e.args[0])
                return

            try:
                for image_name in self.IMAGE_NAMES:
                    if os.path.exists(file_path + image_name):
                        self.__compress_image(file_path + image_name, config)
                        web_client.files_upload(channels=channel_id, file=file_path + image_name)
                        break
                else:
                    web_client.chat_postMessage(channel=channel_id, text="Archive must contain image.png or image.jpg file")
            except ConfigParseError:
                web_client.chat_postMessage(channel=channel_id, text="Could not compress image")

        else:
            web_client.chat_postMessage(channel=channel_id, text="Could not download file")

    @staticmethod
    def __parse_config(config_path):
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
    def __compress_image(image_path, config):
        image = Image.open(image_path)
        resized_image = image.resize((config["width"], config["height"]), Image.ANTIALIAS)
        if config["make_bw"]:
            resized_image = resized_image.convert("L")
        resized_image.save(image_path)


class ConfigParseError(Exception):
    pass
