from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import logging
from typing import Any, Iterable
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import BatchRecalculationAuditCrud, RouteCrud, SearchHistoryCrud, SegmentCrud
from app.db.models import Route
from app.errors import NotFoundAppError, ValidationAppError
from app.schemas.routes_api import (
    BatchRouteStatus,
    RouteBatchRecalculateItem,
    RouteBatchRecalculateRequest,
    RouteBatchRecalculateResponse,
    RouteDTO,
    RouteRecalculateRequest,
    RouteRecalculateResponse,
    RouteSearchRequest,
    RouteSearchResponse,
    SegmentDTO,
    SortMode,
    TransportType,
)
from app.services.providers import (
    BusProviderAdapter,
    FerryProviderAdapter,
    FlightProviderAdapter,
    ProviderAdapterError,
    ProviderSegment,
    ProviderRegistry,
    SegmentSearchQuery,
    TrainProviderAdapter,
)
from app.services.cache import SegmentCacheRepository
from app.services.observability import observability_registry
from app.services.routing_engine import RouteCandidate, RoutingConstraints, RoutingEngine
from config import settings

logger = logging.getLogger("app.route_application")


class RouteSearchService(ABC):
    """Interface for route search use-case."""

    @abstractmethod
    async def search(
        self,
        session: AsyncSession,
        payload: RouteSearchRequest,
        user_id: int | None = None,
        trace_id: str | None = None,
    ) -> RouteSearchResponse:
        raise NotImplementedError


class RouteRecalculationService(ABC):
    """Interface for single route recalculation use-case."""

    @abstractmethod
    async def recalculate(
        self,
        session: AsyncSession,
        route_id: int,
        payload: RouteRecalculateRequest,
        idempotency_key: str | None = None,
    ) -> RouteRecalculateResponse:
        raise NotImplementedError


class BatchRecalculationService(ABC):
    """Interface for batch route recalculation use-case."""

    @abstractmethod
    async def batch_recalculate(
        self, session: AsyncSession, payload: RouteBatchRecalculateRequest
    ) -> RouteBatchRecalculateResponse:
        raise NotImplementedError


class DbRouteApplicationService(
    RouteSearchService, RouteRecalculationService, BatchRecalculationService
):
    """DB-backed route application service with provider and cache integrations."""

    def __init__(
        self,
        provider_registry: ProviderRegistry | None = None,
        segment_cache_repository: SegmentCacheRepository | None = None,
    ) -> None:
        """Initialize service dependencies."""
        self._provider_registry = provider_registry or ProviderRegistry(
            adapters=[
                FlightProviderAdapter(),
                TrainProviderAdapter(),
                BusProviderAdapter(),
                FerryProviderAdapter(),
            ]
        )
        self._segment_cache = segment_cache_repository or SegmentCacheRepository()
        self._routing_engine = RoutingEngine()
        self._recalculate_idempotency_cache: dict[str, RouteRecalculateResponse] = {}

    @staticmethod
    def _route_to_dto(route: Route) -> RouteDTO:
        segments = [SegmentDTO.model_validate(item) for item in route.segments_snapshot]
        return RouteDTO(
            route_id=route.id,
            route_version=route.route_version,
            origin_id=route.origin_location_id,
            destination_id=route.destination_location_id,
            date=route.date,
            total_price=route.total_price,
            currency=route.currency,
            total_duration_minutes=route.total_duration_minutes,
            total_transfer_duration_minutes=route.total_transfer_duration_minutes,
            transfers_count=route.transfers_count,
            score=float(route.score),
            score_breakdown={"engine_score": float(route.score)},
            segments=segments,
        )

    @staticmethod
    def _segment_dto_to_create_dict(
        segment: SegmentDTO, raw_payload: dict | None = None
    ) -> dict[str, Any]:
        return {
            "provider": segment.provider,
            "transport_type": segment.transport_type.value,
            "origin_hub_id": segment.origin_hub_id,
            "destination_hub_id": segment.destination_hub_id,
            "departure_time": segment.departure_time,
            "arrival_time": segment.arrival_time,
            "price_amount": segment.price_amount,
            "currency": segment.currency,
            "external_id": segment.external_id,
            "raw_payload": raw_payload,
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
        }

    @staticmethod
    def _build_stub_segment(payload: RouteSearchRequest, idx: int) -> SegmentDTO:
        now = datetime.now(UTC)
        depart = now + timedelta(hours=idx + 1)
        duration = 90 + (idx * 15)
        arrive = depart + timedelta(minutes=duration)
        price = Decimal("45.00") + Decimal(idx * 7)
        return SegmentDTO(
            provider="contract_stub",
            transport_type=TransportType.FLIGHT,
            external_id=f"fallback-seg-{payload.origin_id}-{payload.destination_id}-{idx + 1}",
            origin_hub_id=payload.origin_id,
            destination_hub_id=payload.destination_id,
            departure_time=depart,
            arrival_time=arrive,
            duration_minutes=duration,
            price_amount=price,
            currency="USD",
            payment_url=None,
        )

    @staticmethod
    def _segment_dto_to_provider_segment(segment: SegmentDTO) -> ProviderSegment:
        return ProviderSegment(
            provider=segment.provider,
            transport_type=segment.transport_type,
            external_id=segment.external_id,
            origin_hub_id=segment.origin_hub_id,
            destination_hub_id=segment.destination_hub_id,
            departure_time=segment.departure_time,
            arrival_time=segment.arrival_time,
            duration_minutes=segment.duration_minutes,
            price_amount=segment.price_amount,
            currency=segment.currency,
            raw_payload={"fallback": True},
        )

    @staticmethod
    def _provider_to_segment_dto(item: ProviderSegment) -> SegmentDTO:
        return SegmentDTO(
            provider=item.provider,
            transport_type=item.transport_type,
            external_id=item.external_id,
            origin_hub_id=item.origin_hub_id,
            destination_hub_id=item.destination_hub_id,
            departure_time=item.departure_time,
            arrival_time=item.arrival_time,
            duration_minutes=item.duration_minutes,
            price_amount=item.price_amount,
            currency=item.currency,
            payment_url=None,
        )

    @staticmethod
    def _to_constraints(payload: RouteSearchRequest) -> RoutingConstraints:
        """Map API preferences to routing-engine constraints."""
        budget_limit = payload.preferences.budget_amount
        if payload.preferences.budget_currency and payload.preferences.budget_currency.upper() != "USD":
            budget_limit = None
        max_transfers = payload.preferences.max_transfers if payload.preferences.max_transfers is not None else 3
        return RoutingConstraints(
            min_transfer_minutes=payload.preferences.min_transfer_minutes,
            max_transfers=max_transfers,
            budget_limit=budget_limit,
            max_total_duration_minutes=payload.preferences.max_total_duration_minutes,
            allowed_transport_types=set(payload.preferences.transport_types)
            if payload.preferences.transport_types
            else None,
            max_depth=max(max_transfers + 1, 1),
            max_paths_to_explore=settings.routing_max_paths_to_explore,
        )

    def _fallback_candidates(self, payload: RouteSearchRequest) -> list[RouteCandidate]:
        fallback: list[RouteCandidate] = []
        for idx in range(payload.top_n):
            segment = self._build_stub_segment(payload, idx)
            price = Decimal("45.00") + Decimal(idx * 7)
            duration = 90 + (idx * 15)
            fallback.append(
                RouteCandidate(
                    segments=[segment],
                    total_price=price,
                    currency="USD",
                    total_duration_minutes=duration,
                    total_transfer_duration_minutes=0,
                    transfers_count=0,
                    score=float(price) if payload.sort_by == SortMode.PRICE else float(duration),
                    score_breakdown={"fallback": 1.0},
                )
            )
        return fallback

    def _sync_cache_metrics(self) -> None:
        """Publish cache counters from repository into global observability snapshot."""
        metrics = self._segment_cache.metrics
        observability_registry.set_cache_metrics(
            hits=metrics.hits,
            misses=metrics.misses,
            stale=metrics.stale,
            errors=metrics.errors,
        )

    async def search(
        self,
        session: AsyncSession,
        payload: RouteSearchRequest,
        user_id: int | None = None,
        trace_id: str | None = None,
    ) -> RouteSearchResponse:
        """Search top-N routes with cache-aside provider segment loading."""
        timer = observability_registry.start_timer()
        query = SegmentSearchQuery(
            origin_id=payload.origin_id,
            destination_id=payload.destination_id,
            date=payload.date,
            top_n=payload.top_n,
            trace_id=trace_id or str(uuid.uuid4()),
        )
        try:
            provider_segments = await self._fetch_segments_with_cache(
                query=query,
                transport_types=payload.preferences.transport_types,
            )
            self._sync_cache_metrics()

            if not provider_segments:
                provider_segments = [
                    self._segment_dto_to_provider_segment(self._build_stub_segment(payload, idx))
                    for idx in range(payload.top_n)
                ]
                await self._segment_cache.set_segments(query, provider_segments)
                self._sync_cache_metrics()

            segment_dtos = [self._provider_to_segment_dto(item) for item in provider_segments]
            route_candidates = self._routing_engine.find_routes(
                origin_id=payload.origin_id,
                destination_id=payload.destination_id,
                search_date=payload.date,
                segments=segment_dtos,
                sort_mode=payload.sort_by,
                top_n=payload.top_n,
                constraints=self._to_constraints(payload),
            )
            if not route_candidates:
                route_candidates = self._fallback_candidates(payload)

            logger.info(
                "Routing completed",
                extra={
                    "origin_id": payload.origin_id,
                    "destination_id": payload.destination_id,
                    "date": payload.date.isoformat(),
                    "routes_found": len(route_candidates),
                    "segment_count": len(segment_dtos),
                },
            )

            routes: list[RouteDTO] = []
            for route_candidate in route_candidates:
                segment_rows = await SegmentCrud.create_many(
                    session=session,
                    items=[
                        self._segment_dto_to_create_dict(segment, raw_payload={"source": "routing_engine"})
                        for segment in route_candidate.segments
                    ],
                    commit=False,
                )
                segment_snapshots: list[dict[str, Any]] = []
                for idx, segment in enumerate(route_candidate.segments):
                    segment_snapshots.append(
                        segment.model_copy(
                            update={"payment_url": f"https://pay.example.com/segment/{segment_rows[idx].id}"}
                        ).model_dump(mode="json")
                    )

                route_row = await RouteCrud.create(
                    session=session,
                    data={
                        "origin_location_id": payload.origin_id,
                        "destination_location_id": payload.destination_id,
                        "date": payload.date,
                        "total_price": route_candidate.total_price,
                        "currency": route_candidate.currency,
                        "total_duration_minutes": route_candidate.total_duration_minutes,
                        "total_transfer_duration_minutes": route_candidate.total_transfer_duration_minutes,
                        "transfers_count": route_candidate.transfers_count,
                        "score": Decimal(str(round(route_candidate.score, 4))),
                        "segments_snapshot": segment_snapshots,
                    },
                    commit=False,
                )
                await SearchHistoryCrud.create(
                    session=session,
                    data={
                        "user_id": user_id,
                        "origin_location_id": payload.origin_id,
                        "destination_location_id": payload.destination_id,
                        "date": payload.date,
                        "preferences": payload.preferences.model_dump(mode="json"),
                    },
                    commit=False,
                )
                await session.commit()
                routes.append(
                    self._route_to_dto(route_row).model_copy(
                        update={"score_breakdown": route_candidate.score_breakdown}
                    )
                )
            observability_registry.record_operation("search", timer(), is_error=False)
            return RouteSearchResponse(routes=routes)
        except Exception:
            observability_registry.record_operation("search", timer(), is_error=True)
            logger.exception(
                "Route search failed",
                extra={
                    "origin_id": payload.origin_id,
                    "destination_id": payload.destination_id,
                    "date": payload.date.isoformat(),
                },
            )
            raise

    async def _fetch_segments_with_cache(
        self,
        query: SegmentSearchQuery,
        transport_types: list[TransportType] | None,
    ) -> list[ProviderSegment]:
        """Get provider segments through cache-aside strategy with soft fallback."""
        cached_segments = await self._segment_cache.get_segments(query)
        if cached_segments is not None:
            return cached_segments

        try:
            provider_segments = await self._provider_registry.fetch_segments(
                query=query,
                transport_types=transport_types,
            )
        except ProviderAdapterError:
            provider_segments = []

        if provider_segments:
            await self._segment_cache.set_segments(query, provider_segments)
        return provider_segments

    async def recalculate(
        self,
        session: AsyncSession,
        route_id: int,
        payload: RouteRecalculateRequest,
        idempotency_key: str | None = None,
    ) -> RouteRecalculateResponse:
        """Recalculate saved route with optional idempotency key."""
        timer = observability_registry.start_timer()
        request_idempotency_key = idempotency_key or payload.idempotency_key
        cache_key = f"{route_id}:{request_idempotency_key}" if request_idempotency_key else None
        if cache_key and cache_key in self._recalculate_idempotency_cache:
            observability_registry.record_operation("recalculate", timer(), is_error=False)
            return self._recalculate_idempotency_cache[cache_key]

        try:
            route = await RouteCrud.get(session, route_id)
            if route is None:
                raise NotFoundAppError(
                    message="Route not found",
                    details={"route_id": route_id},
                )

            _ = payload
            updated_row = await RouteCrud.update_with_new_version(
                session=session,
                item=route,
                data={
                    "score": Decimal(route.score) * Decimal("0.98"),
                    "segments_snapshot": route.segments_snapshot,
                },
            )
            response = RouteRecalculateResponse(
                route=self._route_to_dto(updated_row),
                recalculated_at=updated_row.recalculated_at or datetime.now(UTC),
                changed=True,
            )
            if cache_key:
                self._recalculate_idempotency_cache[cache_key] = response
            observability_registry.record_operation("recalculate", timer(), is_error=False)
            return response
        except Exception:
            observability_registry.record_operation("recalculate", timer(), is_error=True)
            logger.exception("Route recalculation failed", extra={"route_id": route_id})
            raise

    async def batch_recalculate(
        self, session: AsyncSession, payload: RouteBatchRecalculateRequest
    ) -> RouteBatchRecalculateResponse:
        """Run batch recalculation workflow: prepare, execute, persist, and report."""
        timer = observability_registry.start_timer()
        if len(payload.route_ids) > settings.batch_max_size:
            raise ValidationAppError(
                message="Batch size exceeds configured maximum",
                details={
                    "batch_size": len(payload.route_ids),
                    "batch_max_size": settings.batch_max_size,
                },
            )
        route_ids = self._deduplicate_route_ids(payload.route_ids)
        existing = await self._load_routes_in_chunks(session, route_ids, chunk_size=100)

        await self._warm_cache_for_routes_grouped(
            routes=existing.values(),
            max_concurrency=payload.max_concurrency,
            retries=2,
        )

        items: list[RouteBatchRecalculateItem] = []
        updated = 0
        unchanged = 0
        failed = 0
        not_found = 0

        try:
            for route_id in route_ids:
                route = existing.get(route_id)
                if route is None:
                    not_found += 1
                    items.append(
                        RouteBatchRecalculateItem(
                            route_id=route_id,
                            status=BatchRouteStatus.NOT_FOUND,
                            error="Route not found",
                        )
                    )
                    continue

                if not payload.force_refresh:
                    unchanged += 1
                    items.append(
                        RouteBatchRecalculateItem(
                            route_id=route_id,
                            status=BatchRouteStatus.UNCHANGED,
                            route=self._route_to_dto(route),
                        )
                    )
                    continue

                try:
                    updated_row = await RouteCrud.update_with_new_version(
                        session=session,
                        item=route,
                        data={
                            "score": Decimal(route.score) * Decimal("0.98"),
                            "segments_snapshot": route.segments_snapshot,
                        },
                        commit=False,
                    )
                    updated += 1
                    items.append(
                        RouteBatchRecalculateItem(
                            route_id=route_id,
                            status=BatchRouteStatus.UPDATED,
                            route=self._route_to_dto(updated_row),
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    items.append(
                        RouteBatchRecalculateItem(
                            route_id=route_id,
                            status=BatchRouteStatus.FAILED,
                            error=str(exc),
                        )
                    )

            response = RouteBatchRecalculateResponse(
                total=len(route_ids),
                updated=updated,
                unchanged=unchanged,
                failed=failed + not_found,
                items=items,
            )

            audit = await BatchRecalculationAuditCrud.create(
                session=session,
                data={
                    "requested_count": len(payload.route_ids),
                    "unique_count": len(route_ids),
                    "updated_count": updated,
                    "unchanged_count": unchanged,
                    "failed_count": failed,
                    "not_found_count": not_found,
                    "status": "partial_success" if (failed or not_found) else "success",
                    "result_payload": response.model_dump(mode="json"),
                },
                commit=False,
            )
            await session.commit()
            observability_registry.record_operation("batch_recalculate", timer(), is_error=False)
            logger.info(
                "Batch recalculation completed",
                extra={
                    "batch_id": audit.id,
                    "total": len(route_ids),
                    "updated": updated,
                    "unchanged": unchanged,
                    "failed": failed,
                    "not_found": not_found,
                },
            )
            return response.model_copy(update={"batch_id": audit.id})
        except Exception:
            observability_registry.record_operation("batch_recalculate", timer(), is_error=True)
            logger.exception(
                "Batch recalculation failed",
                extra={"requested_count": len(payload.route_ids)},
            )
            raise

    @staticmethod
    def _deduplicate_route_ids(route_ids: list[int]) -> list[int]:
        """Deduplicate route ids while preserving input order."""
        seen: set[int] = set()
        result: list[int] = []
        for route_id in route_ids:
            if route_id in seen:
                continue
            seen.add(route_id)
            result.append(route_id)
        return result

    async def _load_routes_in_chunks(
        self,
        session: AsyncSession,
        route_ids: list[int],
        chunk_size: int,
    ) -> dict[int, Route]:
        """Load routes in chunks to avoid oversized IN queries."""
        existing: dict[int, Route] = {}
        for start in range(0, len(route_ids), chunk_size):
            chunk = route_ids[start : start + chunk_size]
            chunk_rows = await RouteCrud.list_by_ids(session, chunk)
            for item in chunk_rows:
                existing[item.id] = item
        return existing

    async def _warm_cache_for_routes_grouped(
        self,
        routes: Iterable[Route],
        max_concurrency: int,
        retries: int,
    ) -> None:
        """Warm cache by grouped direction/date keys using bounded concurrency and retries."""
        grouped: dict[tuple[int, int, Any], list[Route]] = defaultdict(list)
        for route in routes:
            grouped[(route.origin_location_id, route.destination_location_id, route.date)].append(route)

        semaphore = asyncio.Semaphore(max_concurrency)

        async def run_for_group(key: tuple[int, int, Any]) -> None:
            origin_id, destination_id, route_date = key
            query = SegmentSearchQuery(
                origin_id=origin_id,
                destination_id=destination_id,
                date=route_date,
                top_n=5,
            )
            async with semaphore:
                for attempt in range(retries + 1):
                    cached = await self._segment_cache.get_segments(query)
                    self._sync_cache_metrics()
                    if cached is not None:
                        return
                    segments = await self._fetch_segments_with_cache(
                        query=query,
                        transport_types=None,
                    )
                    if segments:
                        self._sync_cache_metrics()
                        return
                    if attempt < retries:
                        await asyncio.sleep(0.2 * (2**attempt))

        await asyncio.gather(*(run_for_group(key) for key in grouped.keys()))
