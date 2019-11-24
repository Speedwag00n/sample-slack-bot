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
            except Exception as ex:
                web_client.chat_postMessage(channel=channel_id, text=ex.args[0])
                return

            try:
                if os.path.exists(file_path + "/image.png"):
                    self.__compress_image(file_path + "/image.png", config)
                    web_client.files_upload(channels=channel_id, file=file_path + "/image.png")
                elif os.path.exists(file_path + "/image.jpg"):
                    self.__compress_image(file_path + "/image.jpg", config)
                    web_client.files_upload(channels=channel_id, file=file_path + "/image.jpg")
                else:
                    web_client.chat_postMessage(channel=channel_id, text="Archive must contain image.png or image.jpg file")
            except Exception:
                web_client.chat_postMessage(channel=channel_id, text="Could not compress image")

        else:
            web_client.chat_postMessage(channel=channel_id, text="Could not download file")

    @staticmethod
    def __parse_config(config_path):
        try:
            with open(config_path) as config:
                config_data = json.load(config)
        except FileNotFoundError:
            raise Exception("Archive must contain config.json file with compressing configuration")

        try:
            width = int(config_data["size_x"])
        except ValueError:
            raise Exception("Field \"size_x\" must be an integer")
        except KeyError:
            raise Exception("Config must contain \"size_x\" field")

        try:
            height = int(config_data["size_y"])
        except ValueError:
            raise Exception("Field \"size_y\" must be an integer")
        except KeyError:
            raise Exception("Config must contain \"size_y\" field")

        return {"width": width, "height": height}

    @staticmethod
    def __compress_image(image_path, config):
        image = Image.open(image_path)
        resized_image = image.resize((config["width"], config["height"]), Image.ANTIALIAS)
        resized_image.save(image_path)
