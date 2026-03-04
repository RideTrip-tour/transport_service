"""In-process observability registry for transport service."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from statistics import quantiles
from time import perf_counter
from typing import Callable


@dataclass(slots=True)
class OperationStats:
    """Aggregated counters and latency samples for service operation."""

    calls: int = 0
    errors: int = 0
    latency_ms: list[float] = field(default_factory=list)


@dataclass(slots=True)
class ProviderStats:
    """Provider-level SLA counters and latency samples."""

    calls: int = 0
    errors: int = 0
    latency_ms: list[float] = field(default_factory=list)


class ObservabilityRegistry:
    """Mutable metrics storage used by API handlers and services."""

    def __init__(self) -> None:
        """Initialize empty metric registries."""
        self._operations: dict[str, OperationStats] = defaultdict(OperationStats)
        self._providers: dict[str, ProviderStats] = defaultdict(ProviderStats)
        self._error_codes: dict[str, int] = defaultdict(int)
        self._cache_metrics: dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "stale": 0,
            "errors": 0,
        }

    def start_timer(self) -> Callable[[], float]:
        """Return callback that computes elapsed milliseconds."""
        started = perf_counter()

        def elapsed_ms() -> float:
            return (perf_counter() - started) * 1000

        return elapsed_ms

    def record_operation(self, operation: str, latency_ms: float, is_error: bool = False) -> None:
        """Record operation latency and optional failure."""
        stats = self._operations[operation]
        stats.calls += 1
        stats.latency_ms.append(latency_ms)
        if is_error:
            stats.errors += 1

    def record_provider_call(self, provider: str, latency_ms: float, is_error: bool = False) -> None:
        """Record provider call latency and optional failure."""
        stats = self._providers[provider]
        stats.calls += 1
        stats.latency_ms.append(latency_ms)
        if is_error:
            stats.errors += 1

    def record_error_code(self, code: str) -> None:
        """Increment app error code counter."""
        self._error_codes[code] += 1

    def set_cache_metrics(self, *, hits: int, misses: int, stale: int, errors: int) -> None:
        """Store cache counters for hit-ratio calculations."""
        self._cache_metrics = {
            "hits": hits,
            "misses": misses,
            "stale": stale,
            "errors": errors,
        }

    @staticmethod
    def _latency_snapshot(values: list[float]) -> dict[str, float]:
        """Build latency stats with p95/p99 when enough samples are available."""
        if not values:
            return {"avg_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}
        avg = sum(values) / len(values)
        if len(values) < 2:
            return {"avg_ms": round(avg, 2), "p95_ms": round(values[0], 2), "p99_ms": round(values[0], 2)}
        q = quantiles(values, n=100, method="inclusive")
        return {
            "avg_ms": round(avg, 2),
            "p95_ms": round(q[94], 2),
            "p99_ms": round(q[98], 2),
        }

    def snapshot(self) -> dict:
        """Return JSON-serializable metrics snapshot."""
        operations = {}
        for name, stats in self._operations.items():
            ops_error_rate = (stats.errors / stats.calls) if stats.calls else 0.0
            operations[name] = {
                "calls": stats.calls,
                "errors": stats.errors,
                "error_rate": round(ops_error_rate, 4),
                "latency": self._latency_snapshot(stats.latency_ms),
            }

        providers = {}
        for name, stats in self._providers.items():
            providers[name] = {
                "calls": stats.calls,
                "errors": stats.errors,
                "error_rate": round((stats.errors / stats.calls), 4) if stats.calls else 0.0,
                "latency": self._latency_snapshot(stats.latency_ms),
                "sla_success_rate": round(((stats.calls - stats.errors) / stats.calls), 4)
                if stats.calls
                else 0.0,
            }

        return {
            "operations": operations,
            "providers": providers,
            "error_codes": dict(self._error_codes),
            "cache": {
                **self._cache_metrics,
                "hit_ratio": round(
                    (
                        self._cache_metrics["hits"]
                        / (self._cache_metrics["hits"] + self._cache_metrics["misses"])
                    ),
                    4,
                )
                if (self._cache_metrics["hits"] + self._cache_metrics["misses"])
                else 0.0,
            },
        }


observability_registry = ObservabilityRegistry()
