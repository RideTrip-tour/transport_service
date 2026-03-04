"""epic 02 data schema

Revision ID: 20260303_0002
Revises: 20260227_0001
Create Date: 2026-03-03 00:00:02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260303_0002"
down_revision = "20260227_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_transport_quotes_provider_name", table_name="transport_quotes")
    op.drop_index("ix_transport_quotes_currency", table_name="transport_quotes")
    op.drop_index("ix_transport_quotes_transport_request_id", table_name="transport_quotes")
    op.drop_table("transport_quotes")

    op.drop_index("ix_transport_requests_arrival_location_id", table_name="transport_requests")
    op.drop_index("ix_transport_requests_departure_location_id", table_name="transport_requests")
    op.drop_index("ix_transport_requests_user_id", table_name="transport_requests")
    op.drop_table("transport_requests")

    op.drop_index("ix_catalog_routes_from_to_active", table_name="transport_catalog_routes")
    op.drop_index("ix_catalog_routes_transport_type_id", table_name="transport_catalog_routes")
    op.drop_index("ix_catalog_routes_to_location_id", table_name="transport_catalog_routes")
    op.drop_index("ix_catalog_routes_from_location_id", table_name="transport_catalog_routes")
    op.drop_table("transport_catalog_routes")

    op.drop_table("transport_types")

    op.create_table(
        "segments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("transport_type", sa.String(length=32), nullable=False),
        sa.Column("origin_hub_id", sa.Integer(), nullable=False),
        sa.Column("destination_hub_id", sa.Integer(), nullable=False),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("origin_hub_id <> destination_hub_id", name="ck_segments_origin_neq_destination"),
        sa.CheckConstraint("arrival_time > departure_time", name="ck_segments_arrival_gt_departure"),
        sa.CheckConstraint("price_amount >= 0", name="ck_segments_price_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_id", name="uq_segments_provider_external_id"),
    )
    op.create_index(
        "ix_segments_origin_destination_departure",
        "segments",
        ["origin_hub_id", "destination_hub_id", "departure_time"],
    )
    op.create_index("ix_segments_expires_at", "segments", ["expires_at"])

    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("route_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("origin_location_id", sa.Integer(), nullable=False),
        sa.Column("destination_location_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("total_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("total_transfer_duration_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transfers_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("segments_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recalculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("origin_location_id <> destination_location_id", name="ck_routes_origin_neq_destination"),
        sa.CheckConstraint("total_price >= 0", name="ck_routes_total_price_non_negative"),
        sa.CheckConstraint("total_duration_minutes > 0", name="ck_routes_total_duration_positive"),
        sa.CheckConstraint("total_transfer_duration_minutes >= 0", name="ck_routes_transfer_duration_non_negative"),
        sa.CheckConstraint("transfers_count >= 0", name="ck_routes_transfers_count_non_negative"),
        sa.CheckConstraint("route_version >= 1", name="ck_routes_version_min_1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_routes_origin_destination_date",
        "routes",
        ["origin_location_id", "destination_location_id", "date"],
    )
    op.create_index("ix_routes_date", "routes", ["date"])
    op.create_index("ix_routes_updated_at", "routes", ["updated_at"])

    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("origin_location_id", sa.Integer(), nullable=False),
        sa.Column("destination_location_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "origin_location_id <> destination_location_id",
            name="ck_search_history_origin_neq_destination",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_history_user_created", "search_history", ["user_id", "created_at"])
    op.create_index(
        "ix_search_history_origin_destination_date",
        "search_history",
        ["origin_location_id", "destination_location_id", "date"],
    )
    op.create_index("ix_search_history_created_at", "search_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_search_history_created_at", table_name="search_history")
    op.drop_index("ix_search_history_origin_destination_date", table_name="search_history")
    op.drop_index("ix_search_history_user_created", table_name="search_history")
    op.drop_table("search_history")

    op.drop_index("ix_routes_updated_at", table_name="routes")
    op.drop_index("ix_routes_date", table_name="routes")
    op.drop_index("ix_routes_origin_destination_date", table_name="routes")
    op.drop_table("routes")

    op.drop_index("ix_segments_expires_at", table_name="segments")
    op.drop_index("ix_segments_origin_destination_departure", table_name="segments")
    op.drop_table("segments")

    op.create_table(
        "transport_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "transport_catalog_routes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transport_type_id", sa.Integer(), nullable=False),
        sa.Column("from_location_id", sa.Integer(), nullable=False),
        sa.Column("to_location_id", sa.Integer(), nullable=False),
        sa.Column("base_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("base_price_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("base_currency", sa.String(length=3), nullable=True),
        sa.Column("provider", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("base_duration_minutes > 0", name="ck_catalog_route_duration_pos"),
        sa.CheckConstraint("from_location_id <> to_location_id", name="ck_catalog_route_from_neq_to"),
        sa.ForeignKeyConstraint(["transport_type_id"], ["transport_types.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_catalog_routes_from_location_id",
        "transport_catalog_routes",
        ["from_location_id"],
    )
    op.create_index(
        "ix_catalog_routes_to_location_id",
        "transport_catalog_routes",
        ["to_location_id"],
    )
    op.create_index(
        "ix_catalog_routes_transport_type_id",
        "transport_catalog_routes",
        ["transport_type_id"],
    )
    op.create_index(
        "ix_catalog_routes_from_to_active",
        "transport_catalog_routes",
        ["from_location_id", "to_location_id", "is_active"],
    )

    op.create_table(
        "transport_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("transport_type_id", sa.Integer(), nullable=True),
        sa.Column("departure_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrival_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("departure_location_id", sa.Integer(), nullable=False),
        sa.Column("arrival_location_id", sa.Integer(), nullable=False),
        sa.Column("passenger_count", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("passenger_count > 0", name="ck_transport_request_passenger_count_pos"),
        sa.CheckConstraint("departure_location_id <> arrival_location_id", name="ck_transport_request_from_neq_to"),
        sa.ForeignKeyConstraint(["transport_type_id"], ["transport_types.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transport_requests_user_id", "transport_requests", ["user_id"])
    op.create_index(
        "ix_transport_requests_departure_location_id",
        "transport_requests",
        ["departure_location_id"],
    )
    op.create_index(
        "ix_transport_requests_arrival_location_id",
        "transport_requests",
        ["arrival_location_id"],
    )

    op.create_table(
        "transport_quotes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transport_request_id", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(length=128), nullable=False),
        sa.Column("external_quote_id", sa.String(length=128), nullable=True),
        sa.Column("price_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_url", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["transport_request_id"], ["transport_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_transport_quotes_transport_request_id",
        "transport_quotes",
        ["transport_request_id"],
    )
    op.create_index("ix_transport_quotes_currency", "transport_quotes", ["currency"])
    op.create_index("ix_transport_quotes_provider_name", "transport_quotes", ["provider_name"])

