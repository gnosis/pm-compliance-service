from typing import Dict


class BaseClient:
    def __init__(self, base_url: str, token: str):
        self._base_url = base_url
        self._token = token

    def get_auth_header(self) -> Dict:
        """
        Creates the authorization header to set on each request
        :return: auth header dictionary
        """
        return {
            'Authorization': f'Token token={self._token}'
        }
