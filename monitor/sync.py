import os
import time

from . import config
from .db import Metadata
from .events import to_relayer_request, filter_events
from .logger import logger
from .providers import get_providers
from .transaction import build_batch_unwrap, submit_batch
from .utils import chunk_list


CONFIRMATIONS = 6
SLEEP_TIME = 60 * 5


def sync(providers, sleep_time=60 * 10):
    private_key = os.environ["PRIVATE_KEY"]
    account_address = os.environ["ACCOUNT_ADDRESS"]

    while True:
        for provider in providers:
            _p = provider

            balance = providers[_p]["contract"].functions.balance().call()
            bridge_balance = providers[_p]["provider"].eth.get_balance(
                providers[_p]["contract"].address
            )
            print("balance:", balance, bridge_balance, bridge_balance - balance)

            if balance != bridge_balance:
                tx = (
                    providers[_p]["contract"]
                    .functions.sync()
                    .build_transaction(
                        {
                            "nonce": providers[_p][
                                "provider"
                            ].eth.get_transaction_count(account_address),
                            "from": account_address,
                        }
                    )
                )
                signed_tx = providers[_p]["provider"].eth.account.sign_transaction(
                    tx, private_key
                )
                tx_hash = providers[_p]["provider"].eth.send_raw_transaction(
                    signed_tx.rawTransaction
                )
                print(f"sync {_p}:", tx_hash.hex())

        time.sleep(sleep_time)


def run():
    providers = get_providers(config)
    while True:
        try:
            sync(providers, sleep_time=60)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("EXCEPTION:", e)
            time.sleep(SLEEP_TIME)
