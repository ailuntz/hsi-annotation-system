"""Simple in-memory rate limiting for authentication endpoints."""

import time
from collections import defaultdict
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, status


@dataclass
class RateLimitEntry:
    """Rate limit entry for tracking requests."""

    attempts: int = 0
    window_start: float = field(default_factory=time.time)


class RateLimiter:
    """Simple in-memory rate limiter.

    Note: This implementation is suitable for single-instance deployments.
    For multi-instance deployments, use Redis-based rate limiting.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 300,  # 5 minutes
        block_seconds: int = 900,  # 15 minutes
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds
        self._entries: dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._blocked: dict[str, float] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup_old_entries(self) -> None:
        """Clean up expired entries to prevent memory leak."""
        current_time = time.time()
        # Clean up old rate limit entries
        expired_keys = [
            key
            for key, entry in self._entries.items()
            if current_time - entry.window_start > self.window_seconds
        ]
        for key in expired_keys:
            del self._entries[key]

        # Clean up expired blocks
        expired_blocks = [
            key
            for key, block_time in self._blocked.items()
            if current_time - block_time > self.block_seconds
        ]
        for key in expired_blocks:
            del self._blocked[key]

    def check(self, request: Request) -> None:
        """Check if the request is rate limited.

        Raises:
            HTTPException: If rate limit exceeded.
        """
        self._cleanup_old_entries()
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Check if blocked
        if client_ip in self._blocked:
            block_time = self._blocked[client_ip]
            remaining = self.block_seconds - (current_time - block_time)
            if remaining > 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed attempts. Please try again in {int(remaining)} seconds.",
                )
            else:
                del self._blocked[client_ip]

        # Get or create entry
        entry = self._entries[client_ip]

        # Reset window if expired
        if current_time - entry.window_start > self.window_seconds:
            entry.attempts = 0
            entry.window_start = current_time

    def record_attempt(self, request: Request, success: bool = False) -> None:
        """Record an authentication attempt.

        Args:
            request: The request object.
            success: Whether the attempt was successful.
        """
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        if success:
            # Clear on successful login
            if client_ip in self._entries:
                del self._entries[client_ip]
            if client_ip in self._blocked:
                del self._blocked[client_ip]
            return

        # Record failed attempt
        entry = self._entries[client_ip]
        if current_time - entry.window_start > self.window_seconds:
            entry.attempts = 1
            entry.window_start = current_time
        else:
            entry.attempts += 1

        # Block if exceeded
        if entry.attempts >= self.max_attempts:
            self._blocked[client_ip] = current_time
            del self._entries[client_ip]


# Global rate limiter instance for auth endpoints
auth_rate_limiter = RateLimiter(
    max_attempts=5,  # 5 failed attempts
    window_seconds=300,  # within 5 minutes
    block_seconds=900,  # block for 15 minutes
)
