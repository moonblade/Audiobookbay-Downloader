from abb.torrent import QBittorrentClient


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


class FakeSession:
    def __init__(self, response, cookie_name=None):
        self.response = response
        self.cookies = {}
        if cookie_name:
            self.cookies[cookie_name] = "session-id"
        self.requests = []

    # **kwargs absorbs transport-level options such as timeout, which the
    # assertions below deliberately ignore.
    def post(self, url, data=None, headers=None, **kwargs):
        self.requests.append({"url": url, "data": data, "headers": headers})
        return self.response


def test_qbittorrent_login_accepts_v5_no_content_response_with_session_cookie():
    client = QBittorrentClient(
        url="http://qbittorrent.local",
        username="user",
        password="pass",
    )
    client.session = FakeSession(FakeResponse(204), cookie_name="QBT_SID")

    assert client._login() is True
    assert client._logged_in is True
    assert client.session.requests == [
        {
            "url": "http://qbittorrent.local/api/v2/auth/login",
            "data": {"username": "user", "password": "pass"},
            "headers": {"Referer": "http://qbittorrent.local"},
        }
    ]


def test_qbittorrent_login_rejects_no_content_response_without_session_cookie():
    client = QBittorrentClient(
        url="http://qbittorrent.local",
        username="user",
        password="pass",
    )
    client.session = FakeSession(FakeResponse(204))

    assert client._login() is False
    assert client._logged_in is False
