import requests
from app.constants import FINNPLUS_DOMAIN


def fetcher():
    r = requests.get(f'{FINNPLUS_DOMAIN}/fetch_articles')
    print(r.status_code)