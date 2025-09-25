import requests


class Office:
    def __init__(self, tenant_id, content_type, publisher_id, token):
        self.content_type = content_type
        self.publisher_id = publisher_id
        self.token = token
        self.base_url = f"https://manage.office.com/api/v1.0/{tenant_id}/activity/feed/"

        self._init_session()

    def _init_session(self):
        self.session = requests.session()
        self.session.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method, url, data=None, params=None, response_json=True):
        r = self.session.request(method, url, json=data, params=params)

        if response_json:
            return r.json()
        else:
            return r

    def list_blobs(self, start_time, end_time):
        url = self.base_url + "/subscriptions/content"
        params = {
            "contentType": self.content_type,
            "PublisherIdentifier": self.publisher_id,
            "startTime": start_time,
            "endTime": end_time,
        }

        r = self._request("GET", url, params=params, response_json=False)

        while "NextPageUri" in r.headers:
            next_page = r.headers["NextPageUri"]
            yield r.json()

            r = self._request("GET", next_page)

        else:
            yield r.json()

    def get_content(self, url):
        r = self._request("GET", url)

        return r
