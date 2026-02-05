import time
from src.workflow.error_handling import CircuitBreaker, RetryStrategy, FallbackStrategy

def test_retry_strategy_enum():
    """Test RetryStrategy has all required values"""
    assert RetryStrategy.NO_RETRY.value == "no_retry"
    assert RetryStrategy.FIXED_DELAY.value == "fixed_delay"
    assert RetryStrategy.EXPONENTIAL_BACKOFF.value == "exponential_backoff"
    assert RetryStrategy.JITTERED_BACKOFF.value == "jittered_backoff"
    assert RetryStrategy.CIRCUIT_BREAKER.value == "circuit_breaker"

def test_fallback_strategy_enum():
    """Test FallbackStrategy has all required values"""
    assert FallbackStrategy.CACHE.value == "cache"
    assert FallbackStrategy.DEFAULT.value == "default"
    assert FallbackStrategy.GRACEFUL_DEGRADATION.value == "graceful"
    assert FallbackStrategy.MANUAL_OVERRIDE.value == "manual"
    assert FallbackStrategy.QUEUE_FOR_LATER.value == "queue"

def test_circuit_breaker_initial_state():
    """Test CircuitBreaker starts in CLOSED state"""
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0

def test_circuit_breaker_open_on_failures():
    """Test CircuitBreaker opens after threshold failures"""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
    
    # Record 3 failures
    for _ in range(3):
        cb.record_failure()
    
    assert cb.state == "OPEN"
    assert cb.failure_count == 3
    
    # Should not allow requests when OPEN
    assert cb.allow_request() is False

def test_circuit_breaker_half_open_after_timeout():
    """Test CircuitBreaker goes to HALF_OPEN after timeout"""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
    
    cb.record_failure()
    assert cb.state == "OPEN"
    
    # Wait for timeout
    time.sleep(0.15)
    
    # Should allow request and go to HALF_OPEN
    assert cb.allow_request() is True
    assert cb.state == "HALF_OPEN"

def test_circuit_breaker_reset_on_success():
    """Test CircuitBreaker resets on success"""
    cb = CircuitBreaker(failure_threshold=3)
    
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "CLOSED"  # Still closed, 2 < 3
    
    cb.record_success()
    assert cb.failure_count == 0
