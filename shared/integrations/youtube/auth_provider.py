import pickle

from pathlib import Path

from googleapiclient.discovery import (
    build
)

from google_auth_oauthlib.flow import (
    InstalledAppFlow
)

from google.auth.transport.requests import (
    Request
)


class YouTubeAuthProvider:

    def __init__(

        self,

        client_secret_file: Path,

        token_dir: Path,

        scopes: list[str]
    ):

        self.client_secret_file = (
            Path(client_secret_file)
        )

        self.token_dir = (
            Path(token_dir)
        )

        self.scopes = scopes

        self.token_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    # =====================================
    # TOKEN PATH
    # =====================================

    def get_token_path(
        self,
        channel_id: str
    ) -> Path:

        return (
            self.token_dir
            / f"{channel_id}.pickle"
        )

    # =====================================
    # AUTH SERVICE
    # =====================================

    def get_authenticated_service(
        self,
        channel_id: str
    ):

        token_path = (
            self.get_token_path(
                channel_id
            )
        )

        creds = None

        # =================================
        # LOAD CACHE
        # =================================

        if token_path.exists():

            with open(
                token_path,
                "rb"
            ) as f:

                creds = pickle.load(f)

        # =================================
        # REFRESH / LOGIN
        # =================================

        if not creds or not creds.valid:

            if (
                creds
                and creds.expired
                and creds.refresh_token
            ):

                print(
                    "[YouTubeAuth] "
                    "Refreshing token..."
                )

                creds.refresh(Request())

            else:

                print(
                    "[YouTubeAuth] "
                    "OAuth login required"
                )

                flow = (
                    InstalledAppFlow
                    .from_client_secrets_file(

                        str(
                            self.client_secret_file
                        ),

                        self.scopes
                    )
                )

                creds = flow.run_local_server(

                    port=0,

                    prompt="select_account"
                )

            # =============================
            # SAVE TOKEN
            # =============================

            with open(
                token_path,
                "wb"
            ) as f:

                pickle.dump(
                    creds,
                    f
                )

            print(
                "[YouTubeAuth] "
                f"Saved token: "
                f"{token_path}"
            )

        # =================================
        # BUILD SERVICE
        # =================================

        return build(
            "youtube",
            "v3",
            credentials=creds
        )