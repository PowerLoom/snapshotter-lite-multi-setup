from pydantic import BaseModel, Field
from typing import Dict, Set, List

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
    compute: ComputeConfig
    config: ComputeConfig

class PowerloomChainConfig(BaseModel):
    powerloomChain: ChainConfig
    dataMarkets: List[MarketConfig]

class ChainMarketData(BaseModel):
    chain_config: ChainConfig
    markets: Dict[str, MarketConfig]

class CLIContext(BaseModel):
    markets_config: List[PowerloomChainConfig]  # Now properly typed
    chain_markets_map: Dict[str, ChainMarketData]
    available_environments: Set[str]
    available_markets: Set[str] 

