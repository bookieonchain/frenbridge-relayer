from .db import Metadata, Submitted
from .logger import logger


class Event:
    def __init__(self, provider, contract):
        self.web3 = provider
        self.contract = contract
        self.initialized = False

    def fetch(self, from_block=0, to_block="latest"):
        self.event_filter = self.contract.events.LockedToken.create_filter(
            fromBlock=from_block,
            toBlock=to_block,
        )
        return self.event_filter.get_all_entries()


def to_relayer_request(
    token, amount, recipient, target_chain_id, block_num, proposal_index
):
    # RelayerRequest
    return {
        "token": token,
        "amount": amount,
        "recipient": recipient,
        "targetChainId": target_chain_id,
        "transactionBlockNumber": block_num,
        "_proposalIndex": proposal_index,
    }


def filter_events(events, provider, contract, m, account_address):
    filtered_events = []
    # TODO: assumes that it's going to the other chain
    for event in events:
        token = event["args"]["token"]
        amount = event["args"]["amount"]
        recipient = event["args"]["recipient"]
        target_chain_id = event["args"]["targetChainId"]
        transaction_block_number = event["args"]["blockNumber"]
        proposal_index = event["args"]["proposalIndex"]

        hashed_proposal = contract.functions.hashProposal(
            {
                "token": token,
                "amount": amount,
                "recipient": recipient,
                "targetChainId": target_chain_id,
                "transactionBlockNumber": transaction_block_number,
                "_proposalIndex": proposal_index,
            }
        ).call()
        _vote_count, completed = contract.functions.__proposals(hashed_proposal).call()
        has_voted = contract.functions.hasVoted(hashed_proposal, account_address).call()

        if completed or has_voted:
            logger.info(
                f"skipping event {event['transactionHash'].hex()} because it's complete"
            )
            submitted_proposal = (
                Submitted.filter()
                .where(Submitted.hashed_proposal == hashed_proposal)
                .first()
            )
            if submitted_proposal is None:
                s = Submitted.create(
                    tx_hash=None,
                    source_chain_id=provider,
                    hashed_proposal=hashed_proposal,
                    success=True,
                )
                s.save()

                Metadata.update(
                    last_block=max(transaction_block_number - 1, m.last_block)
                ).where(Metadata.id == m.id).execute()
            continue

        filtered_events.append(event)

    return filtered_events
