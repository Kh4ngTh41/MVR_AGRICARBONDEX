from config import Config
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(Config.WEB3_PROVIDER_URI))
print("Connected:", w3.is_connected())
