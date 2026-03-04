from __future__ import annotations

import dataclasses
from datetime import date
from decimal import Decimal
import logging
from typing import Iterable

from app.schemas.routes_api import SegmentDTO, SortMode, TransportType

logger = logging.getLogger("app.routing_engine")


@dataclasses.dataclass(slots=True)
class RoutingConstraints:
    min_transfer_minutes: int = 20
    max_transfers: int = 3
    budget_limit: Decimal | None = None
    max_total_duration_minutes: int | None = None
    allowed_transport_types: set[TransportType] | None = None
    max_depth: int = 4
    max_paths_to_explore: int = 5000


@dataclasses.dataclass(slots=True)
class RouteCandidate:
    segments: list[SegmentDTO]
    total_price: Decimal
    currency: str
    total_duration_minutes: int
    total_transfer_duration_minutes: int
    transfers_count: int
    score: float
    score_breakdown: dict[str, float]


class RoutingEngine:
    """In-memory multi-criteria route search with guardrails."""

    def find_routes(
        self,
        *,
        origin_id: int,
        destination_id: int,
        search_date: date,
        segments: Iterable[SegmentDTO],
        sort_mode: SortMode,
        top_n: int,
        constraints: RoutingConstraints,
    ) -> list[RouteCandidate]:
        """Build route candidates and return sorted top-N list."""
        prepared = [
            segment
            for segment in segments
            if segment.origin_hub_id != segment.destination_hub_id
            and segment.departure_time.date() == search_date
            and segment.arrival_time > segment.departure_time
            and segment.duration_minutes > 0
            and (
                constraints.allowed_transport_types is None
                or segment.transport_type in constraints.allowed_transport_types
            )
        ]
        adjacency: dict[int, list[SegmentDTO]] = {}
        for segment in prepared:
            adjacency.setdefault(segment.origin_hub_id, []).append(segment)
        for key in adjacency:
            adjacency[key].sort(
                key=lambda seg: (seg.departure_time, seg.arrival_time, seg.price_amount)
            )

        explored_paths = 0
        raw_routes: list[RouteCandidate] = []

        def dfs(path: list[SegmentDTO], visited_hubs: set[int]) -> None:
            nonlocal explored_paths
            if explored_paths >= constraints.max_paths_to_explore:
                logger.warning(
                    "Routing exploration guardrail reached",
                    extra={"max_paths_to_explore": constraints.max_paths_to_explore},
                )
                return
            explored_paths += 1

            if path:
                current_hub = path[-1].destination_hub_id
            else:
                current_hub = origin_id

            if len(path) > constraints.max_depth:
                return

            for next_segment in adjacency.get(current_hub, []):
                if path:
                    prev_segment = path[-1]
                    layover = int(
                        (next_segment.departure_time - prev_segment.arrival_time).total_seconds()
                        // 60
                    )
                    if layover < constraints.min_transfer_minutes:
                        continue
                else:
                    layover = 0

                if path and next_segment.destination_hub_id in visited_hubs:
                    continue

                new_path = [*path, next_segment]
                total_price = sum(item.price_amount for item in new_path)
                if constraints.budget_limit is not None and total_price > constraints.budget_limit:
                    continue

                total_duration = int(
                    (new_path[-1].arrival_time - new_path[0].departure_time).total_seconds()
                    // 60
                )
                if (
                    constraints.max_total_duration_minutes is not None
                    and total_duration > constraints.max_total_duration_minutes
                ):
                    continue

                transfers = max(len(new_path) - 1, 0)
                if transfers > constraints.max_transfers:
                    continue

                if next_segment.destination_hub_id == destination_id:
                    transfer_duration = 0
                    for idx in range(1, len(new_path)):
                        transfer_duration += int(
                            (
                                new_path[idx].departure_time - new_path[idx - 1].arrival_time
                            ).total_seconds()
                            // 60
                        )
                    raw_routes.append(
                        RouteCandidate(
                            segments=new_path,
                            total_price=total_price,
                            currency=new_path[0].currency,
                            total_duration_minutes=total_duration,
                            total_transfer_duration_minutes=max(transfer_duration, 0),
                            transfers_count=transfers,
                            score=0.0,
                            score_breakdown={},
                        )
                    )
                    continue

                new_visited = set(visited_hubs)
                new_visited.add(next_segment.destination_hub_id)
                dfs(new_path, new_visited)

        dfs(path=[], visited_hubs={origin_id})
        if not raw_routes:
            return []

        price_min = min(float(item.total_price) for item in raw_routes)
        price_max = max(float(item.total_price) for item in raw_routes)
        duration_min = min(item.total_duration_minutes for item in raw_routes)
        duration_max = max(item.total_duration_minutes for item in raw_routes)

        def normalize(value: float, min_value: float, max_value: float) -> float:
            if max_value == min_value:
                return 0.0
            return (value - min_value) / (max_value - min_value)

        ranked: list[RouteCandidate] = []
        for candidate in raw_routes:
            price_norm = normalize(float(candidate.total_price), price_min, price_max)
            duration_norm = normalize(
                float(candidate.total_duration_minutes),
                float(duration_min),
                float(duration_max),
            )
            if sort_mode == SortMode.PRICE:
                score = float(candidate.total_price)
                breakdown = {"price": float(candidate.total_price), "duration": float(candidate.total_duration_minutes)}
            elif sort_mode == SortMode.TIME:
                score = float(candidate.total_duration_minutes)
                breakdown = {"duration": float(candidate.total_duration_minutes), "price": float(candidate.total_price)}
            else:
                score = duration_norm * 0.6 + price_norm * 0.4
                breakdown = {
                    "duration_norm": duration_norm,
                    "price_norm": price_norm,
                    "duration_weight": 0.6,
                    "price_weight": 0.4,
                }
            ranked.append(
                RouteCandidate(
                    segments=candidate.segments,
                    total_price=candidate.total_price,
                    currency=candidate.currency,
                    total_duration_minutes=candidate.total_duration_minutes,
                    total_transfer_duration_minutes=candidate.total_transfer_duration_minutes,
                    transfers_count=candidate.transfers_count,
                    score=score,
                    score_breakdown=breakdown,
                )
            )

        if sort_mode == SortMode.PRICE:
            ranked.sort(
                key=lambda item: (
                    item.total_price,
                    item.total_duration_minutes,
                    item.transfers_count,
                    tuple(seg.external_id for seg in item.segments),
                )
            )
        elif sort_mode == SortMode.TIME:
            ranked.sort(
                key=lambda item: (
                    item.total_duration_minutes,
                    item.total_price,
                    item.transfers_count,
                    tuple(seg.external_id for seg in item.segments),
                )
            )
        else:
            ranked.sort(
                key=lambda item: (
                    item.score,
                    item.total_duration_minutes,
                    item.total_price,
                    tuple(seg.external_id for seg in item.segments),
                )
            )
        return ranked[:top_n]
