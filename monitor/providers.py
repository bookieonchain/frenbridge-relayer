import json

from web3 import Web3
from web3.middleware import geth_poa_middleware

from .db import Metadata
from .events import Event
from .utils import chunk_list


def get_providers(config):
    with open("abi.json") as f:
        abi = json.loads(f.read())

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
            "target_chain_id": config["chains"][chain]["target_chain_id"],
        }

        if not (
            m := Metadata.select()
            .where(Metadata.id == 1 and Metadata.chain_id == provider)
            .first()
        ):
            Metadata.create(chain_id=provider, last_block=0)

    return providers
