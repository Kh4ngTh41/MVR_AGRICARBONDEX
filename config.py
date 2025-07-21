import os
from web3 import Web3

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET", "supersecretkey")  # Đọc từ biến môi trường
    WEB3_PROVIDER_URI = os.getenv("WEB3_URI", "https://sepolia.era.zksync.dev")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # private key của owner
    PUBLIC_ADDRESS = os.getenv("PUBLIC_ADDRESS")  # address của owner

    # Contract addresses on Sepolia
    CCT_ADDRESS = os.getenv("CCT_ADDRESS", "0xd354672b949Cf71C91463a7a96025cD66742e52B")
    DEBT_NFT_ADDRESS = os.getenv("DEBT_NFT_ADDRESS", "0xa8C0520a74E6Fccd939915A869409Dff0f0751Ed")
    OFFSET_NFT_ADDRESS = os.getenv("OFFSET_NFT_ADDRESS", "0x7d224A65C39FC3bAded73B4cAe38487a07b314a3")

    # ABI paths
    ABI_PATHS = {
        "CCT": os.getenv("CCT_ABI_PATH", "abis/CarbonCreditToken.json"),
        "DEBT": os.getenv("DEBT_ABI_PATH", "abis/CarbonDebtNFT.json"),
        "OFFSET": os.getenv("OFFSET_ABI_PATH", "abis/CarbonOffsetNFT.json")
    }

web3 = Web3(Web3.HTTPProvider(Config.WEB3_PROVIDER_URI))
