import json
from pathlib import Path


CHANNELS_DIR = (
    Path(__file__).resolve().parent
    / "channels"
)


class ChannelConfigLoader:

    @staticmethod
    def load(
        channel_id: str
    ):

        config_path = (
            CHANNELS_DIR
            / f"{channel_id}.json"
        )

        if not config_path.exists():

            raise FileNotFoundError(
                f"Missing channel config: "
                f"{config_path}"
            )

        with open(
            config_path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)