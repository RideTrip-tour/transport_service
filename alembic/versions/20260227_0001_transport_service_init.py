"""transport service initial schema

Revision ID: 20260227_0001
Revises:
Create Date: 2026-02-27 00:00:01
"""

from alembic import op
import sqlalchemy as sa
revision = "20260227_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
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


def downgrade() -> None:
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
