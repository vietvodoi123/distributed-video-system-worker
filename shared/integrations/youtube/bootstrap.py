from pathlib import Path

from shared.integrations.youtube.auth_provider import (
    YouTubeAuthProvider
)

from shared.integrations.youtube.youtube_api import (
    YouTubeAPI
)

from shared.utils.settings import (
    load_yaml_settings
)

from shared.runtime.artifacts.artifact_paths import (
    get_project_root
)


settings = load_yaml_settings()

project_root = (
    get_project_root()
)

youtube_auth_provider = (
    YouTubeAuthProvider(

        client_secret_file=
        project_root / settings[
            "CLIENT_SECRET_FILE"
        ],

        token_dir=
        project_root / "data/tokens",

        scopes=[

            "https://www.googleapis.com/auth/youtube.upload",

            "https://www.googleapis.com/auth/youtube",
        ]
    )
)

youtube_api = (
    YouTubeAPI(

        api_key=
        settings["API_KEY"],

        auth_provider=
        youtube_auth_provider
    )
)