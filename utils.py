import json
from config import Config, web3

def load_contract(name, address):
    with open(Config.ABI_PATHS[name], "r") as f:
        abi = json.load(f)["abi"]
    return web3.eth.contract(address=address, abi=abi)

def build_tx(tx):
    tx["from"] = Config.PUBLIC_ADDRESS
    tx["nonce"] = web3.eth.get_transaction_count(Config.PUBLIC_ADDRESS)
    tx["gas"] = 3000000
    tx["gasPrice"] = web3.to_wei("20", "gwei")
    signed = web3.eth.account.sign_transaction(tx, private_key=Config.PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    return web3.to_hex(tx_hash)
