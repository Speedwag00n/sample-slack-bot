import os
import logging
import slack
import commands.command_manager as command_manager
import commands.standard


@slack.RTMClient.run_on(event="message")
def message(**payload):
    data = payload["data"]
    keys = command_manager.CommandManager().commands
    channel_id = data["channel"]
    web_client = payload["web_client"]
    try:
        if data["subtype"] == "bot_message":
            return
    except KeyError:
        pass
    if not str(data["text"]).startswith(commands.standard.COMMAND_PREFIX):
        return
    keyword = str(data["text"].split(" ", maxsplit=1)[0]).lower()[1::]
    try:
        command = keys[keyword]
        try:
            command.execute(payload)
        except Exception as e:
            logger.exception(e)
            web_client.chat_postMessage(channel=channel_id, text="Unexpected error happened")
    except KeyError:
        web_client.chat_postMessage(channel=channel_id, text="Unknown command. Please, use help command")


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    token = os.environ["SLACK_SAMPLE_BOT_TOKEN"]
    rtm_client = slack.RTMClient(token=token)
    rtm_client.start()
