from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Set, List, Optional
from pathlib import Path
import os

class ChainConfig(BaseModel):
    name: str
    chainId: int
    rpcURL: HttpUrl

class ComputeConfig(BaseModel):
    repo: HttpUrl
    branch: str
    commit: Optional[str] = None

class ConfigRepoConfig(BaseModel):
    repo: HttpUrl
    branch: str
    commit: Optional[str] = None

class MarketConfig(BaseModel):
    name: str
    sourceChain: str
    contractAddress: str
    powerloomProtocolStateContractAddress: str
    compute: ComputeConfig
    config: ConfigRepoConfig
    sequencer: str

class PowerloomChainConfig(BaseModel):
    powerloomChain: ChainConfig
    dataMarkets: List[MarketConfig]

class ChainMarketData(BaseModel):
    chain_config: ChainConfig
    markets: Dict[str, MarketConfig]

# New model for storing identity specific to a chain
class ChainSpecificIdentity(BaseModel):
    wallet_address: Optional[str] = None
    signer_account_address: Optional[str] = None
    signer_account_private_key: Optional[str] = None # Stored as plain text

class UserSettings(BaseModel):
    default_powerloom_chain: Optional[str] = None
    chain_identities: Dict[str, ChainSpecificIdentity] = Field(default_factory=dict)
    source_chain_rpcs: Dict[str, HttpUrl] = Field(default_factory=dict)

    @classmethod
    def get_settings_path(cls) -> Path:
        # Using XDG Base Directory Specification for user config
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config_home:
            return Path(xdg_config_home) / "powerloom-cli" / "settings.json"
        return Path.home() / ".config" / "powerloom-cli" / "settings.json"

class CLIContext(BaseModel):
    markets_config: List[PowerloomChainConfig]
    chain_markets_map: Dict[str, ChainMarketData]
    available_environments: Set[str] # These are the valid chain names (UPPERCASE)
    available_markets: Set[str] 
    user_settings: UserSettings

    class Config:
        arbitrary_types_allowed = True

