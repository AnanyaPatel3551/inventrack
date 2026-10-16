from alembic import op
import sqlalchemy as sa

revision = "0001_create_products"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="General"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0"),
        sa.Column("supplier", sa.String(length=150), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="IN_STOCK"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)

def downgrade():
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
