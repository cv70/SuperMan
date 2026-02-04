"""SuperMan AI 公司配置模块

此模块负责从 config.yaml 加载和管理所有配置。
配置完全通过 YAML 文件加载，不依赖环境变量。
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """LLM 模型配置（支持任意兼容 OpenAI API 格式的模型）"""

    name: str = "gpt-4"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    default: bool = False
    capabilities: list = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    provider: str = "openai"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        """从字典创建 ModelConfig"""
        return cls(
            name=data.get("name", "gpt-4"),
            base_url=data.get("base_url", "https://api.openai.com/v1"),
            model=data.get("model", data.get("name", "gpt-4")),
            api_key=data.get("api_key"),
            default=data.get("default", False),
            capabilities=data.get("capabilities", []),
            config=data.get("config", {}),
            provider=data.get("provider", "openai"),
        )


@dataclass
class LLMConfig:
    """LLM 配置"""

    models: Dict[str, ModelConfig] = field(default_factory=dict)
    default_model: str = "gpt-4"

    def __post_init__(self):
        """初始化后处理"""
        if not self.models:
            self.models = {}
            default_config = ModelConfig(name=self.default_model)
            self.models[self.default_model] = default_config

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        """从字典创建 LLMConfig"""
        models = {}
        models_list = data.get("models", [])
        for model_data in models_list:
            model = ModelConfig.from_dict(model_data)
            models[model.name] = model

        return cls(
            models=models,
            default_model=data.get("default_model", "gpt-4"),
        )


@dataclass
class AgentConfig:
    """智能体配置"""

    model: str = "gpt-4"
    temperature: float = 0.3

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """从字典创建 AgentConfig"""
        return cls(
            model=data.get("model", "gpt-4"),
            temperature=float(data.get("temperature", 0.3)),
        )


@dataclass
class CommunicationConfig:
    """通信协议配置"""

    timeout: Dict[str, int] = field(default_factory=dict)
    retry: Dict[str, int] = field(default_factory=dict)
    qos: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommunicationConfig":
        """从字典创建 CommunicationConfig"""
        return cls(
            timeout=data.get("timeout", {"default": 30}),
            retry=data.get("retry", {"max_attempts": 3}),
            qos=data.get("qos", {}),
        )


@dataclass
class WorkflowConfig:
    """工作流配置"""

    state_graph: Dict[str, Any] = field(default_factory=dict)
    scheduling: Dict[str, Any] = field(default_factory=dict)
    automated_workflows: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowConfig":
        """从字典创建 WorkflowConfig"""
        return cls(
            state_graph=data.get("state_graph", {}),
            scheduling=data.get("scheduling", {}),
            automated_workflows=data.get("automated_workflows", []),
        )


@dataclass
class SecurityConfig:
    """安全配置"""

    api_keys: Dict[str, Any] = field(default_factory=dict)
    access_control: Dict[str, Any] = field(default_factory=dict)
    data_protection: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityConfig":
        """从字典创建 SecurityConfig"""
        return cls(
            api_keys=data.get("api_keys", {}),
            access_control=data.get("access_control", {}),
            data_protection=data.get("data_protection", {}),
        )


@dataclass
class LoggingConfig:
    """日志配置"""

    level: str = "INFO"
    format: str = "JSON"
    output: list = field(default_factory=list)
    file: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoggingConfig":
        """从字典创建 LoggingConfig"""
        return cls(
            level=data.get("level", "INFO"),
            format=data.get("format", "JSON"),
            output=data.get("output", []),
            file=data.get("file", {}),
        )


@dataclass
class MetricsConfig:
    """指标收集配置"""

    enabled: bool = True
    interval: int = 60
    collectors: list = field(default_factory=list)
    endpoints: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricsConfig":
        """从字典创建 MetricsConfig"""
        return cls(
            enabled=data.get("enabled", True),
            interval=data.get("interval", 60),
            collectors=data.get("collectors", []),
            endpoints=data.get("endpoints", []),
        )


@dataclass
class AlertChannelConfig:
    """告警通道配置"""

    type: str = ""
    recipients: list = field(default_factory=list)
    webhook_url: Optional[str] = None
    channels: list = field(default_factory=list)
    threshold: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertChannelConfig":
        """从字典创建 AlertChannelConfig"""
        return cls(
            type=data.get("type", ""),
            recipients=data.get("recipients", []),
            webhook_url=data.get("webhook_url"),
            channels=data.get("channels", []),
            threshold=data.get("threshold", {}),
        )


@dataclass
class AlertsConfig:
    """告警配置"""

    enabled: bool = True
    channels: list = field(default_factory=list)
    severity_levels: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertsConfig":
        """从字典创建 AlertsConfig"""
        return cls(
            enabled=data.get("enabled", True),
            channels=[
                AlertChannelConfig.from_dict(ch) for ch in data.get("channels", [])
            ],
            severity_levels=data.get("severity_levels", {}),
        )


@dataclass
class MonitoringConfig:
    """监控和日志配置"""

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitoringConfig":
        """从字典创建 MonitoringConfig"""
        return cls(
            logging=LoggingConfig.from_dict(data.get("logging", {})),
            metrics=MetricsConfig.from_dict(data.get("metrics", {})),
            alerts=AlertsConfig.from_dict(data.get("alerts", {})),
        )


@dataclass
class ConcurrencyConfig:
    """并发配置"""

    max_workers: int = 10
    task_queue_size: int = 100
    batch_size: int = 10

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConcurrencyConfig":
        """从字典创建 ConcurrencyConfig"""
        return cls(
            max_workers=data.get("max_workers", 10),
            task_queue_size=data.get("task_queue_size", 100),
            batch_size=data.get("batch_size", 10),
        )


@dataclass
class CachingConfig:
    """缓存配置"""

    enabled: bool = True
    ttl_seconds: int = 300
    memory_limit_mb: int = 100
    backend: str = "redis"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachingConfig":
        """从字典创建 CachingConfig"""
        return cls(
            enabled=data.get("enabled", True),
            ttl_seconds=data.get("ttl_seconds", 300),
            memory_limit_mb=data.get("memory_limit_mb", 100),
            backend=data.get("backend", "redis"),
        )


@dataclass
class DatabaseConfig:
    """数据库配置"""

    type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    name: str = "superman"
    user: str = "superman"
    password: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 5

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatabaseConfig":
        """从字典创建 DatabaseConfig"""
        return cls(
            type=data.get("type", "postgresql"),
            host=data.get("host", "localhost"),
            port=data.get("port", 5432),
            name=data.get("name", "superman"),
            user=data.get("user", "superman"),
            password=data.get("password"),
            pool_size=data.get("pool_size", 10),
            max_overflow=data.get("max_overflow", 5),
        )


@dataclass
class RedisConfig:
    """Redis 配置"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RedisConfig":
        """从字典创建 RedisConfig"""
        return cls(
            host=data.get("host", "localhost"),
            port=data.get("port", 6379),
            db=data.get("db", 0),
            password=data.get("password"),
        )


@dataclass
class PerformanceConfig:
    """性能配置"""

    concurrency: ConcurrencyConfig = field(default_factory=ConcurrencyConfig)
    caching: CachingConfig = field(default_factory=CachingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceConfig":
        """从字典创建 PerformanceConfig"""
        return cls(
            concurrency=ConcurrencyConfig.from_dict(data.get("concurrency", {})),
            caching=CachingConfig.from_dict(data.get("caching", {})),
            database=DatabaseConfig.from_dict(data.get("database", {})),
            redis=RedisConfig.from_dict(data.get("redis", {})),
        )


@dataclass
class StorageConfig:
    """存储配置"""

    base_path: str = "data"
    backup_interval_hours: int = 24
    retention_days: int = 30

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorageConfig":
        """从字典创建 StorageConfig"""
        return cls(
            base_path=data.get("base_path", "data"),
            backup_interval_hours=data.get("backup_interval_hours", 24),
            retention_days=data.get("retention_days", 30),
        )


@dataclass
class FileStorageConfig:
    """文件存储配置"""

    file_system: StorageConfig = field(default_factory=StorageConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileStorageConfig":
        """从字典创建 FileStorageConfig"""
        return cls(
            file_system=StorageConfig.from_dict(data.get("file_system", {})),
        )


@dataclass
class SMTPConfig:
    """SMTP 邮件配置"""

    host: str = "smtp.example.com"
    port: int = 587
    use_tls: bool = True
    user: str = "no-reply@example.com"
    password: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SMTPConfig":
        """从字典创建 SMTPConfig"""
        return cls(
            host=data.get("host", "smtp.example.com"),
            port=data.get("port", 587),
            use_tls=data.get("use_tls", True),
            user=data.get("user", "no-reply@example.com"),
            password=data.get("password"),
        )


@dataclass
class EmailConfig:
    """邮件配置"""

    smtp: SMTPConfig = field(default_factory=SMTPConfig)
    from_address: str = "no-reply@example.com"
    reply_to: str = "support@example.com"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailConfig":
        """从字典创建 EmailConfig"""
        return cls(
            smtp=SMTPConfig.from_dict(data.get("smtp", {})),
            from_address=data.get("from_address", "no-reply@example.com"),
            reply_to=data.get("reply_to", "support@example.com"),
        )


@dataclass
class IntegrationConfig:
    """第三方集成配置"""

    openai: Dict[str, Any] = field(default_factory=dict)
    anthropic: Dict[str, Any] = field(default_factory=dict)
    slack: Dict[str, Any] = field(default_factory=dict)
    database: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationConfig":
        """从字典创建 IntegrationConfig"""
        return cls(
            openai=data.get("openai", {}),
            anthropic=data.get("anthropic", {}),
            slack=data.get("slack", {}),
            database=data.get("database", {}),
        )


@dataclass
class OtherConfig:
    """其他配置"""

    storage: FileStorageConfig = field(default_factory=FileStorageConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OtherConfig":
        """从字典创建 OtherConfig"""
        return cls(
            storage=FileStorageConfig.from_dict(data.get("storage", {})),
            email=EmailConfig.from_dict(data.get("email", {})),
            integrations=IntegrationConfig.from_dict(data.get("integrations", {})),
        )


@dataclass
class CompanyConfig:
    """公司配置"""

    name: str = "SuperMan AI Company"
    description: str = "AI多智能体公司架构"
    created_at: str = "2026-02-05"
    strategic_goals: list = field(default_factory=list)
    kpis: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    market_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompanyConfig":
        """从字典创建 CompanyConfig"""
        return cls(
            name=data.get("name", "SuperMan AI Company"),
            description=data.get("description", "AI多智能体公司架构"),
            created_at=data.get("created_at", "2026-02-05"),
            strategic_goals=data.get("strategic_goals", []),
            kpis=data.get("kpis", {}),
            resources=data.get("resources", {}),
            market_data=data.get("market_data", {}),
        )


@dataclass
class AppConfig:
    """完整应用配置"""

    llm: LLMConfig = field(default_factory=LLMConfig)
    company: CompanyConfig = field(default_factory=CompanyConfig)
    agents: Dict[str, AgentConfig] = field(default_factory=dict)
    communication: CommunicationConfig = field(default_factory=CommunicationConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    other: OtherConfig = field(default_factory=OtherConfig)

    @classmethod
    def from_yaml(cls, yaml_path: str | None = None) -> "AppConfig":
        """从 YAML 文件加载配置"""
        if yaml_path is None:
            import os

            yaml_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ),
                "config.yaml",
            )
            if not os.path.exists(yaml_path):
                yaml_path = "config.yaml"

        try:
            import yaml as yaml_module

            with open(yaml_path, "r", encoding="utf-8") as f:
                config_data = yaml_module.safe_load(f)
        except FileNotFoundError:
            config_data = {}
        except Exception:
            config_data = {}

        if not config_data:
            return cls()

        return cls(
            llm=LLMConfig.from_dict(config_data.get("llm", {})),
            company=CompanyConfig.from_dict(config_data.get("company", {})),
            agents={
                name: AgentConfig.from_dict(agent_data)
                for name, agent_data in config_data.get("agents", {}).items()
            },
            communication=CommunicationConfig.from_dict(
                config_data.get("communication", {})
            ),
            workflow=WorkflowConfig.from_dict(config_data.get("workflow", {})),
            security=SecurityConfig.from_dict(config_data.get("security", {})),
            monitoring=MonitoringConfig.from_dict(config_data.get("monitoring", {})),
            performance=PerformanceConfig.from_dict(config_data.get("performance", {})),
            other=OtherConfig.from_dict(config_data.get("other", {})),
        )


app_config: AppConfig = AppConfig.from_yaml()
llm_config = app_config.llm
