import schedule
import time
import functools

import nft
import database
from log_config import setup_logging

logger = setup_logging('scheduler', 'imagenationbot.log')


def time_execution(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = function(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Function {function.__name__} took {end_time - start_time} seconds to execute")
        return result

    return wrapper


def exception_handler(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in function {function.__name__}: {e}")
            return None

    return wrapper


@time_execution
@exception_handler
def sync_chain():
    logger.info("Job Executing!")
    policies = database.get_all_policies()
    logger.debug(f'policies: {policies}')
    address_groups = database.get_all_addresses()
    for user_id, addresses in address_groups.items():
        counts = {}
        for address in addresses:
            for asset in nft.assets_for_address(address):
                for p, entry in policies.items():
                    if asset['unit'].startswith(p):
                        logger.debug(f'policy: {p}, entry: {entry}')
                        for server, role_id in entry.items():
                            if role_id not in counts:
                                counts[role_id] = 0
                            counts[role_id] += 1
        for role, count in counts.items():
            database.add_holding(user_id, role, count)
        database.reset_holding(user_id, list(counts.keys()))
    database.clean_up_holdings()


if __name__ == '__main__':
    schedule.every(20).minutes.do(sync_chain)  # Run every minute

    while True:
        schedule.run_pending()
        time.sleep(3)
