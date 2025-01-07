from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class SnapshotterSettings(BaseModel):
    SOURCE_RPC_URL: str
    SIGNER_ACCOUNT_ADDRESS: str
    SIGNER_ACCOUNT_PRIVATE_KEY: str
    SLOT_ID: str
    SNAPSHOT_CONFIG_REPO: HttpUrl = Field(default="https://github.com/powerloom/snapshotter-configs")
    SNAPSHOT_CONFIG_REPO_BRANCH: str
    SNAPSHOTTER_COMPUTE_REPO: HttpUrl = Field(default="https://github.com/powerloom/snapshotter-computes")
    SNAPSHOTTER_COMPUTE_REPO_BRANCH: str
    DOCKER_NETWORK_NAME: str = ""
    PROST_RPC_URL: str
    DATA_MARKET_CONTRACT: str
    NAMESPACE: str
    POWERLOOM_REPORTING_URL: HttpUrl = Field(default="https://nms-testnet-reporting.powerloom.io")
    PROST_CHAIN_ID: str
    LOCAL_COLLECTOR_PORT: int = 50051
    CORE_API_PORT: int = 8002
    SUBNET_THIRD_OCTET: int = 1
    MAX_STREAM_POOL_SIZE: int = 2
    STREAM_POOL_HEALTH_CHECK_INTERVAL: int = 30
    DATA_MARKET_IN_REQUEST: bool = True
    
    # Optional fields
    IPFS_URL: Optional[str] = None
    IPFS_API_KEY: Optional[str] = None
    IPFS_API_SECRET: Optional[str] = None
    SLACK_REPORTING_URL: Optional[str] = None
    WEB3_STORAGE_TOKEN: Optional[str] = None
    DASHBOARD_ENABLED: Optional[bool] = None
    TELEGRAM_REPORTING_URL: HttpUrl = Field(default="https://tg-testing.powerloom.io/")
    TELEGRAM_CHAT_ID: Optional[str] = None

    class Config:
        frozen = True