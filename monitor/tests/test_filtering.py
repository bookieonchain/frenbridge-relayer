"""
IGNORE, saved temporarily
"""
import json
import os
import time

from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.module import retrieve_blocking_method_call_fn

from db import Metadata, Submitted
from events import Event
from logger import logger

private_key = os.environ["PRIVATE_KEY"]
ACCOUNT_ADDRESS = "0xA9ba877C8C68e0932bFE913c2ba93e444bDb39B3"
CONFIRMATION = 6

with open("abi.json") as f:
    abi = json.loads(f.read())

config = {
    "chains": {
        "GOERLI": {
            "chainId": 5,
            "rpcUrl": "https://goerli.infura.io/v3/f7795288112a4215b6c88a2170a032aa",
            "bridgeAddress": "0xC36511e371347f047Ce9C637A10a1ba48Ae2D8cf",
            "type": "",
        },
        "FRENCHAIN": {
            "chainId": 44444,
            "rpcUrl": "https://rpc-02.frenscan.io",
            "bridgeAddress": "0xd52B06252aF5C473ae5610d94EAB05B8a503a3eb",
            "type": "POA",
        },
    },
}

providers = dict()
for chain in config["chains"]:
    provider = Web3(Web3.HTTPProvider(config["chains"][chain]["rpcUrl"]))
    if config["chains"][chain]["type"] == "POA":
        provider.middleware_onion.inject(geth_poa_middleware, layer=0)

    contract = provider.eth.contract(
        address=config["chains"][chain]["bridgeAddress"],
        abi=abi,
    )
    providers[chain] = {
        "provider": provider,
        "contract": contract,
        "events": Event(
            provider,
            contract,
        ),
    }

    if not (
        m := Metadata.select()
        .where(Metadata.id == 1 and Metadata.chain_id == provider)
        .first()
    ):
        m = Metadata.create(chain_id=provider, last_block=0)


provider = "GOERLI"
block_number = providers[provider]["provider"].eth.get_block("latest")["number"]
if not (
    m := Metadata.select()
    .where(Metadata.id == 1 and Metadata.chain_id == provider)
    .first()
):
    m = Metadata.create(chain_id=provider, last_block=0)

event_filter = providers[provider]["events"].create_filter(
    m.last_block, block_number - CONFIRMATION
)
ef = event_filter.event_filter
print(ef.eth_module.get_filter_logs)
print(ef.eth_module.get_filter_logs(ef.filter_id))
