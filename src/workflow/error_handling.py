import time
from enum import Enum


class RetryStrategy(Enum):
    """重试策略枚举"""
    NO_RETRY = "no_retry"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    JITTERED_BACKOFF = "jittered_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    def allow_request(self) -> bool:
        """Check if request should be allowed"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            # Check if timeout expired
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
                return True
            return False
        else:  # HALF_OPEN
            return self.half_open_calls < self.half_open_max_calls
    
    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class FallbackStrategy(Enum):
    """降级策略"""
    CACHE = "cache"
    DEFAULT = "default"
    GRACEFUL_DEGRADATION = "graceful"
    MANUAL_OVERRIDE = "manual"
    QUEUE_FOR_LATER = "queue"
