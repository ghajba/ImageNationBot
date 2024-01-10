import json
import os
import time
import functools
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from log_config import setup_logging

logger = setup_logging('nft', 'imagenationbot.log')

load_dotenv()

PROJECT_ID = os.environ.get('PROJECT_ID')
headers = {
    'project_id': PROJECT_ID,
}

assets_for_policy = 'https://cardano-mainnet.blockfrost.io/api/v0/assets/policy/{}?page={}'

asset_address = 'https://cardano-mainnet.blockfrost.io/api/v0/assets/{}/addresses'

address_info = 'https://cardano-mainnet.blockfrost.io/api/v0/addresses/{}'

kreate_addresses = ['addr1wxuk2z6g2gq5m2rr9ruhyq3f5mnxpffmcpnqypxtazxtc3sq24p4k', ]

ada_handle_policy_id = 'f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a'

handle_asset_address = 'https://cardano-mainnet.blockfrost.io/api/v0/assets/f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a{}/addresses'

assets_for_stake = 'https://cardano-mainnet.blockfrost.io/api/v0/accounts/{}/addresses/assets?page={}'


class RateLimiter:
    def __init__(self, max_per_second, max_per_day, logger):
        self.max_per_second = max_per_second
        self.max_per_day = max_per_day
        self.calls_made_today = 0
        self.last_called = 0
        self.current_day = datetime.now(timezone.utc).date()
        self.logger = logger

    def __call__(self, function):
        @functools.wraps(function)
        def wrapped_f(*args, **kwargs):
            today = datetime.now(timezone.utc).date()

            # Reset daily count if a new day has started
            if today > self.current_day:
                self.calls_made_today = 0
                self.current_day = today

            # Check daily limit
            if self.calls_made_today >= self.max_per_day:
                self.logger.warn("Daily request limit reached")
                return None

            # Ensure time gap between requests
            while time.time() - self.last_called < 1.0 / self.max_per_second:
                time.sleep(0.01)

            try:
                result = function(*args, **kwargs)
                self.calls_made_today += 1
                self.last_called = time.time()
                self.logger.debug(f'{self.calls_made_today} calls made today')
                return result
            except Exception as e:
                logger.error(f"Exception in function {function.__name__}: {e}")
                return None

        return wrapped_f


# Initialize the rate limiter
rate_limiter = RateLimiter(max_per_second=10, max_per_day=50000, logger=logger)


@rate_limiter
def _make_request(url, headers):
    return requests.get(url, headers=headers)


def get_addresses(policy):
    assets = []
    for i in range(1, 3):
        response = _make_request(assets_for_policy.format(policy, i), headers=headers)
        for asset in response.json():
            if policy in asset['asset']:
                assets.append(asset['asset'])
            if asset['quantity'] != '1':
                logger.debug(json.dumps(asset, indent=4))
    addresses = []
    for asset in assets:
        response = _make_request(asset_address.format(asset), headers=headers)
        for addy_info in response.json():
            if addy_info['address'] in kreate_addresses:
                continue
            addresses.append(addy_info['address'])
    with open(f'{policy}_addresses.txt', 'w') as outfile:
        outfile.write('\n'.join(addresses))
    return addresses


def valid_handle(handle_name):
    response = _make_request(handle_asset_address.format(handle_name[1:].encode('utf-8').hex()), headers=headers)
    if response.status_code != 200 or not response.json():
        logger.info(response.json())
        logger.info(response.status_code)
        return False
    return response.json()[0]['address']


def get_stake_for_address(address):
    response = _make_request(address_info.format(address), headers=headers)
    if response.status_code != 200 or not response.json():
        return None
    stake = response.json()['stake_address']
    return address if stake is None else stake


def valid_address(address_or_handle):
    if not address_or_handle or not address_or_handle.strip():
        return False, None
    if '$' == address_or_handle[0]:
        address = valid_handle(address_or_handle)
        return address, get_stake_for_address(address)
    if address_or_handle.startswith('addr1'):
        return address_or_handle, get_stake_for_address(address_or_handle)
    return False, None


def assets_for_address(stake_address):
    assets = []
    for i in range(1, 100):
        response = _make_request(assets_for_stake.format(stake_address, i), headers=headers)
        if response.status_code != 200 or not response.json():
            break
        assets += response.json()
    return assets
