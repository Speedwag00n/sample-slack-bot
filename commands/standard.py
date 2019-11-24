import commands.command as command
import os
import requests


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

    variants = ["comp", "compress"]

    def execute(self, payload):
        data = payload["data"]
        file_url = data["files"][0]["url_private_download"]
        file_path = "temp/" + data["files"][0]["id"] + "_" + data["files"][0]["name"]
        web_client = payload["web_client"]
        channel_id = data["channel"]
        token = os.environ["SLACK_SAMPLE_BOT_TOKEN"]
        response = requests.get(file_url, headers={"Authorization": "Bearer " + token})
        if response.status_code == 200:
            open(file_path, "wb").write(response.content)
            message = "Compress..."
        else:
            message = "Can't download file"
        web_client.chat_postMessage(
            channel=channel_id,
            text=message,
        )
