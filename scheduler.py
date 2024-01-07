import schedule
import time
import nft
import database
from log_config import setup_logging

logger = setup_logging('scheduler', 'scheduler.log')


def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the exception or take necessary actions
            logger.error(f"An error occurred in {func.__name__}: {e}")

    return wrapper


@exception_handler
def task():
    logger.info("Job Executing!")
    policies = database.get_all_policies()
    addresses = database.get_all_addresses()
    for address in addresses:
        counts = {}
        for asset in nft.assets_for_address(address[0]):
            for p, entry in policies.items():
                if asset['unit'].startswith(p):
                    for server, role_id in entry.items():
                        if role_id not in counts:
                            counts[role_id] = 0
                        counts[role_id] += 1
        for role, count in counts.items():
            database.add_holding(address[1], role, count)
        database.reset_holding(address[1], list(counts.keys()))
    database.clean_up_holdings()


if __name__ == '__main__':
    schedule.every().hour.do(task)  # Run every minute

    while True:
        schedule.run_pending()
        time.sleep(3)
