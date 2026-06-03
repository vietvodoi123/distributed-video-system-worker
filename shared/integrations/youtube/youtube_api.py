import os
import re
import requests

from pathlib import Path
import time

from googleapiclient.errors import (
    ResumableUploadError,
    HttpError
)
from googleapiclient.http import (
    MediaFileUpload
)


class YouTubeAPI:

    def __init__(

        self,

        api_key: str,

        auth_provider
    ):

        self.api_key = api_key

        self.auth_provider = (
            auth_provider
        )

        self.base_url = (
            "https://www.googleapis.com/youtube/v3"
        )

    # =====================================
    # CHANNEL INFO
    # =====================================

    def get_channel_basic_info(
        self,
        channel_id: str
    ):

        url = (
            f"{self.base_url}/channels"
        )

        params = {

            "part":
            "snippet,statistics",

            "id":
            channel_id,

            "key":
            self.api_key
        }

        response = requests.get(
            url,
            params=params
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("items"):
            return None

        channel = data["items"][0]

        return {

            "id":
            channel["id"],

            "name":
            channel["snippet"]["title"],

            "subscribers":
            channel["statistics"].get(
                "subscriberCount"
            ),

            "description":
            channel["snippet"].get(
                "description",
                ""
            ),

            "avatar_url":
            channel["snippet"]
            ["thumbnails"]
            ["high"]["url"]
        }

    # =====================================
    # HANDLE LOOKUP
    # =====================================

    def get_channel_by_handle(
        self,
        handle: str
    ):

        url = (
            f"{self.base_url}/channels"
        )

        params = {

            "part":
            "snippet,statistics",

            "forHandle":
            handle,

            "key":
            self.api_key
        }

        response = requests.get(
            url,
            params=params
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("items"):
            return None

        channel = data["items"][0]

        return {

            "id":
            channel["id"],

            "name":
            channel["snippet"]["title"],

            "subscribers":
            channel["statistics"].get(
                "subscriberCount"
            ),

            "description":
            channel["snippet"].get(
                "description",
                ""
            ),

            "avatar_url":
            channel["snippet"]
            ["thumbnails"]
            ["high"]["url"]
        }

    # =====================================
    # UPLOAD VIDEO
    # =====================================

    def upload_video(

        self,

        channel_id: str,

        video_path: str,

        title: str,

        description: str,

        category_id: str = "22",

        privacy: str = "public",

        thumbnail_path: str | None = None,

        publish_time: str | None = None,

        tags: list[str] | None = None,
    ) -> str | None:

        youtube = (
            self.auth_provider
            .get_authenticated_service(
                channel_id
            )
        )

        request_body = {

            "snippet": {

                "categoryId":
                category_id,

                "title":
                title,

                "description":
                description,
            },

            "status": {

                "privacyStatus":
                privacy
            },
        }

        # =================================
        # TAGS
        # =================================

        if tags:

            request_body["snippet"][
                "tags"
            ] = tags

        # =================================
        # SCHEDULE
        # =================================

        if publish_time:

            request_body["status"][
                "privacyStatus"
            ] = "private"

            request_body["status"][
                "publishAt"
            ] = publish_time

        # =================================
        # MEDIA
        # =================================

        media = MediaFileUpload(

            video_path,

            resumable=True,

            mimetype="video/*"
        )

        request = (
            youtube.videos().insert(

                part="snippet,status",

                body=request_body,

                media_body=media
            )
        )

        print(
            "[YouTubeAPI] "
            "Uploading video..."
        )

        response = None

        retry_count = 0

        max_retries = 5

        while response is None:

            try:

                status, response = (
                    request.next_chunk()
                )

                if status:
                    progress = int(
                        status.progress() * 100
                    )

                    print(

                        "[YouTubeAPI] "

                        f"Upload progress: "

                        f"{progress}%"
                    )

            # =================================
            # RESUMABLE
            # =================================

            except ResumableUploadError as e:

                error_text = str(e)

                print(

                    "[YouTubeAPI] "

                    f"Resumable error: "

                    f"{error_text}"
                )

                # =============================
                # DAILY QUOTA
                # =============================

                if (

                        "Video Uploads per day"
                        in error_text

                        or

                        "quotaExceeded"
                        in error_text

                        or

                        "rateLimitExceeded"
                        in error_text
                ):
                    raise RuntimeError(
                        "YOUTUBE_DAILY_UPLOAD_QUOTA"
                    )

                retry_count += 1

                if retry_count > max_retries:
                    raise

                sleep_time = (
                        retry_count * 10
                )

                print(

                    "[YouTubeAPI] "

                    f"Retrying upload in "

                    f"{sleep_time}s"
                )

                time.sleep(
                    sleep_time
                )

            # =================================
            # HTTP ERROR
            # =================================

            except HttpError as e:

                error_text = str(e)

                print(

                    "[YouTubeAPI] "

                    f"HttpError: "

                    f"{error_text}"
                )

                if e.resp.status == 429:
                    raise RuntimeError(
                        "YOUTUBE_DAILY_UPLOAD_QUOTA"
                    )

                raise

        # =================================
        # RESPONSE VALIDATE
        # =================================

        if not response:
            raise RuntimeError(
                "YouTube upload failed"
            )

        if "id" not in response:
            raise RuntimeError(
                f"Missing video id: "
                f"{response}"
            )

        video_id = response["id"]

        print(

            "[YouTubeAPI] "

            f"Uploaded video: "

            f"{video_id}"
        )
        # =================================
        # THUMBNAIL
        # =================================

        if (
            thumbnail_path
            and os.path.exists(
                thumbnail_path
            )
        ):

            try:

                youtube.thumbnails().set(

                    videoId=video_id,

                    media_body=MediaFileUpload(
                        thumbnail_path
                    )

                ).execute()

                print(
                    "[YouTubeAPI] "
                    "Thumbnail uploaded"
                )

            except Exception as e:

                print(
                    "[YouTubeAPI] "
                    f"Thumbnail failed: "
                    f"{e}"
                )

        return video_id

    # =====================================
    # PLAYLIST
    # =====================================

    def get_or_create_playlist(

        self,

        youtube,

        playlist_name: str,

        description: str = ""
    ):

        request = (
            youtube.playlists().list(

                part=
                "snippet,contentDetails",

                mine=True,

                maxResults=50
            )
        )

        response = request.execute()

        for playlist in response.get(
            "items",
            []
        ):

            if (
                playlist["snippet"]["title"]
                .lower()
                ==
                playlist_name.lower()
            ):

                print(
                    "[YouTubeAPI] "
                    f"Playlist exists: "
                    f"{playlist_name}"
                )

                return playlist["id"]

        print(
            "[YouTubeAPI] "
            f"Creating playlist: "
            f"{playlist_name}"
        )

        playlist = (
            youtube.playlists().insert(

                part="snippet,status",

                body={

                    "snippet": {

                        "title":
                        playlist_name,

                        "description":
                        description,
                    },

                    "status": {

                        "privacyStatus":
                        "public"
                    },
                },
            ).execute()
        )

        return playlist["id"]

    # =====================================
    # ADD TO PLAYLIST
    # =====================================

    def add_video_to_playlist(

        self,

        youtube,

        video_id: str,

        playlist_id: str
    ):

        youtube.playlistItems().insert(

            part="snippet",

            body={

                "snippet": {

                    "playlistId":
                    playlist_id,

                    "resourceId": {

                        "kind":
                        "youtube#video",

                        "videoId":
                        video_id,
                    },
                }
            },

        ).execute()

        print(
            "[YouTubeAPI] "
            f"Added video to playlist: "
            f"{playlist_id}"
        )

    # =====================================
    # HIGH LEVEL UPLOAD
    # =====================================

    def upload_video_with_playlist(

        self,

        channel_id: str,

        video_path: str,

        title: str,

        description: str,

        tags: list[str],

        playlist_name: str,

        playlist_description: str,

        thumbnail_path: str | None = None,

        publish_time: str | None = None,
    ) -> str | None:

        youtube = (
            self.auth_provider
            .get_authenticated_service(
                channel_id
            )
        )

        # =================================
        # TITLE SANITIZE
        # =================================

        max_title_length = 89

        title = title.strip()

        if len(title) > max_title_length:

            title = (
                title[:max_title_length]
                .rsplit(" ", 1)[0]
                + "..."
            )

        # =================================
        # UPLOAD
        # =================================

        video_id = self.upload_video(

            channel_id=
            channel_id,

            video_path=
            video_path,

            title=
            title,

            description=
            description,

            thumbnail_path=
            thumbnail_path,

            publish_time=
            publish_time,

            tags=
            tags
        )

        if not video_id:

            return None

        # =================================
        # PLAYLIST
        # =================================

        playlist_id = (
            self.get_or_create_playlist(

                youtube=
                youtube,

                playlist_name=
                playlist_name,

                description=
                playlist_description
            )
        )

        self.add_video_to_playlist(

            youtube=
            youtube,

            video_id=
            video_id,

            playlist_id=
            playlist_id
        )

        return (
            f"https://www.youtube.com/"
            f"watch?v={video_id}"
        )