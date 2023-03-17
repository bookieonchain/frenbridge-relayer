import os
import time

from web3 import Web3

from .db import Metadata
from .events import to_relayer_request, filter_events
from .logger import logger
from .providers import get_providers
from .transaction import build_batch_unwrap, submit_batch
from .utils import chunk_list

CONFIRMATIONS = 6

config = {
    "chains": {
        "ETHEREUM": {
            "chainId": 1,
            "rpcUrl": "https://mainnet.infura.io/v3/f7795288112a4215b6c88a2170a032aa",
            "bridgeAddress": "0xDEA1B439f99aA1F167deaB39838E6444E8422188",
            "authority": "0x5242F170aEab4d3B6419c64f15B14bbf4949d183",
            "type": "",
            "target_chain_id": "FRENCHAIN",
        },
        # "GOERLI": {
        #     "chainId": 5,
        #     "rpcUrl": "https://goerli.infura.io/v3/cf8543d0aa644b94a73f7131d74fd57b",
        #     "bridgeAddress": "0x7094e9741Fe6C2b9AABC33DA5789482AC4feD54f",
        #     "authority": "0x79Fed0626BC51A6F91F960D10415cfa87E190fA9",
        #     "type": "",
        #     "target_chain_id": "FRENCHAIN",  # this is temporary to simplify logic
        # },
        "FRENCHAIN": {
            "chainId": 44444,
            "rpcUrl": "https://rpc-02.frenscan.io",
            "bridgeAddress": "0x182914F2f7ebd1067f365E0ea0088b317bF7E76b",
            "authority": "0x550fb5e0d6e8cDdb4193FAAbD1609D1a68BD59F2",
            "type": "POA",
            "target_chain_id": "ETHEREUM",  # this is temporary to simplify logic
        },
    },
}


def monitor(providers, sleep_time=60 * 10, min_block=0):
    private_key = os.environ["PRIVATE_KEY"]
    account_address = os.environ["ACCOUNT_ADDRESS"]

    while True:
        for provider in providers:
            block_number = providers[provider]["provider"].eth.get_block("latest")[
                "number"
            ]
            print("block number", block_number)
            if not (
                m := Metadata.select()
                .where(
                    Metadata.id == 1
                    and Metadata.chain_id == provider
                    and Metadata.relayer_id == os.environ.get("RELAYER_ID")
                )
                .first()
            ):
                m = Metadata.create(chain_id=provider, last_block=0)

            event_filter = providers[provider]["events"]

            last_block = m.last_block
            print(last_block)

            events = event_filter.fetch(
                min(last_block, block_number - CONFIRMATIONS - 1),
                block_number - CONFIRMATIONS,
            )
            logger.info(f"events fetch {provider}", extra={"events_len": len(events)})

            target_chain = providers[provider]["target_chain_id"]
            contract = providers[target_chain]["contract"]
            _p = provider
            provider = providers[target_chain]["provider"]
            events = filter_events(events, provider, contract, m, account_address)

            for chunk in chunk_list(events, 15):
                event_lst = []
                for event in chunk:
                    token = event["args"]["token"]
                    amount = event["args"]["amount"]
                    recipient = event["args"]["recipient"]
                    target_chain_id = event["args"]["targetChainId"]
                    transaction_block_number = event["args"]["blockNumber"]
                    proposal_index = event["args"]["proposalIndex"]

                    event_lst.append(
                        to_relayer_request(
                            token,
                            amount,
                            recipient,
                            target_chain_id,
                            transaction_block_number,
                            proposal_index,
                        )
                    )

                if len(event_lst) > 0:
                    print("eventlist", event_lst)
                    tx = build_batch_unwrap(
                        contract,
                        provider,
                        event_lst,
                        account_address,
                    )
                    receipt = submit_batch(provider, tx, private_key)
                    logger.info(
                        "receipt", extra={"hash": receipt["transactionHash"].hex()}
                    )
                    Metadata.update(
                        last_block=max(transaction_block_number - 1, m.last_block)
                    ).where(Metadata.chain_id == target_chain).execute()

            balance = providers[_p]["contract"].functions.balance().call()
            bridge_balance = providers[_p]["provider"].eth.get_balance(
                providers[_p]["contract"].address
            )
            if balance != bridge_balance:
                time.sleep(10)
                tx = (
                    providers[_p]["contract"]
                    .functions.sync()
                    .build_transaction(
                        {
                            "nonce": providers[_p][
                                "provider"
                            ].eth.get_transaction_count(account_address),
                            "from": account_address,
                            "gasPrice": Web3.to_wei("15", "gwei"),
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
            monitor(providers, sleep_time=60 * 10)
        except Exception as e:
            print("EXCEPTION", e)
            time.sleep(60 * 20)
