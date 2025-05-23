from pydantic import BaseModel, Field
from typing import Dict, Set, List, Optional

class ChainConfig(BaseModel):
    name: str
    chainId: int
    rpcURL: str

class ComputeConfig(BaseModel):
    repo: str
    branch: str

class MarketConfig(BaseModel):
    name: str
    sourceChain: str
    contractAddress: str
    powerloomProtocolStateContractAddress: str
    compute: ComputeConfig
    config: ComputeConfig
    sequencer: str

class PowerloomChainConfig(BaseModel):
    powerloomChain: ChainConfig
    dataMarkets: List[MarketConfig]

class ChainMarketData(BaseModel):
    chain_config: ChainConfig
    markets: Dict[str, MarketConfig]

class UserSettings(BaseModel):
    wallet_address: Optional[str] = None
    signer_account_address: Optional[str] = None
    signer_account_private_key: Optional[str] = None # Stored as plain text, ensure user is aware or implement encryption later
    # We can add other user-specific settings here later, e.g.:
    # default_powerloom_chain: Optional[str] = None
    # default_gas_limit: Optional[int] = None

class CLIContext(BaseModel):
    markets_config: List[PowerloomChainConfig]
    chain_markets_map: Dict[str, ChainMarketData]
    available_environments: Set[str]
    available_markets: Set[str]
    user_settings: UserSettings

