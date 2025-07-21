from web3 import Web3
from eth_account import Account  # ✅ import đúng cách cho v6
import json
import os
from dotenv import load_dotenv

load_dotenv()

INFURA_URL = "https://sepolia.era.zksync.dev"
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # Tạo file .env chứa PRIVATE_KEY
PUBLIC_ADDRESS = os.getenv("PUBLIC_ADDRESS")

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Địa chỉ contract đã deploy
CARBON_CREDIT_ADDRESS = "0xe08AD1dEE2562147E68A14C0F5a02579FdCbA1E6"
CARBON_DEBT_ADDRESS = "0x7FB9F74678C0047Ad560bcEB2c85DAa744632779"
CARBON_OFFSET_ADDRESS = "0x83bf15a237256d4aFE1580028302897cBC266ceD"

# Load ABI từ thư mục abis/
with open("abis/CarbonCreditToken.json") as f:
    credit_abi = json.load(f)
with open("abis/CarbonDebtNFT.json") as f:
    debt_abi = json.load(f)
with open("abis/CarbonOffsetNFT.json") as f:
    offset_abi = json.load(f)

credit_contract = w3.eth.contract(
    address=Web3.to_checksum_address(CARBON_CREDIT_ADDRESS),
    abi=credit_abi
)
debt_contract = w3.eth.contract(
    address=Web3.to_checksum_address(CARBON_DEBT_ADDRESS),
    abi=debt_abi
)
offset_contract = w3.eth.contract(
    address=Web3.to_checksum_address(CARBON_OFFSET_ADDRESS),
    abi=offset_abi
)

# Hàm mint ERC20
def mint_erc20(to_address, amount):
    nonce = w3.eth.get_transaction_count(PUBLIC_ADDRESS)
    tx = credit_contract.functions.mint(to_address, amount).build_transaction({
        'from': PUBLIC_ADDRESS,
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': w3.to_wei('20', 'gwei')
    })
    print(PRIVATE_KEY)
    signed_tx = Account.sign_transaction(tx, PRIVATE_KEY)  # ✅ dùng Account từ eth_account
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()

# Mint Debt NFT (emitter)
def mint_debt_nft(to_address, cid_list, did):
    # cid_list là list các cid muốn mint cùng lúc
    nonce = w3.eth.get_transaction_count(PUBLIC_ADDRESS)
    tx = debt_contract.functions.MintDebtNFT(
        to_address,
        cid_list,  # truyền list các cid
        did,
        cid_list  # truyền list các cid
    ).build_transaction({
        'from': PUBLIC_ADDRESS,
        'nonce': nonce,
        'gas': 700000 + 300000 * (len(cid_list)-1),  # tăng gas theo số lượng cid
        'gasPrice': w3.to_wei('10', 'gwei')
    })
    signed_tx = Account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()

# Mint Offset NFT (absorber)
def mint_offset_nft(to_address, cid_list, did):
    nonce = w3.eth.get_transaction_count(PUBLIC_ADDRESS)
    tx = offset_contract.functions.Mint(
        to_address,
        cid_list,
        did,
        cid_list
    ).build_transaction({
        'from': PUBLIC_ADDRESS,
        'nonce': nonce,
        'gas': 700000 + 300000 * (len(cid_list)-1),
        'gasPrice': w3.to_wei('10', 'gwei')
    })
    signed_tx = Account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()
