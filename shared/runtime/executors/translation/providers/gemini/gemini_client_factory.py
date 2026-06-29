from google.genai import Client


class GeminiClientFactory:

    @staticmethod
    def create(api_key: str) -> Client:
        return Client(api_key=api_key)