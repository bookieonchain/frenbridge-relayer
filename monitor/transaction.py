from .logger import logger


def build_batch_unwrap(
    contract,
    provider,
    relayer_request_arr,
    account_address,
):
    return contract.functions.batchUnwrap(relayer_request_arr).build_transaction(
        {
            "nonce": provider.eth.get_transaction_count(account_address),
            "from": account_address,
        }
    )


def build_unwrap(
    providers,
    token,
    amount,
    recipient,
    transaction_block_number,
    target_chain,
    proposal_index,
    account_address,
):
    return (
        providers[target_chain]["contract"]
        .functions.unwrap(
            {
                "token": token.decode("utf-8").rstrip("\x00").encode("utf-8"),
                "amount": amount,
                "recipient": recipient,
                "targetChainId": target_chain,
                "transactionBlockNumber": transaction_block_number,
                "_proposalIndex": proposal_index,
            }
        )
        .build_transaction(
            {
                "nonce": providers[target_chain]["provider"].eth.get_transaction_count(
                    account_address
                ),
                "from": account_address,
                "gas": 21000,
            }
        )
    )


def submit_unwrap(web3, tx, private_key, hashed_proposal):
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    logger.debug(
        "tx_hash",
        extra={"hash": tx_hash, "hashed_proposal": hashed_proposal},
    )
    receipt = web3.eth.web3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info("receipt", extra=dict(receipt))

    return receipt


def submit_batch(web3, tx, private_key):
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info("receipt", extra=dict(receipt))

    return receipt
