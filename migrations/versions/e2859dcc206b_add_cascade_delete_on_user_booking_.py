"""Add cascade delete on user-booking relationship

Revision ID: e2859dcc206b
Revises: 04f512b1b82e
Create Date: 2025-08-23 14:52:08.044368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2859dcc206b'
down_revision = '04f512b1b82e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("booking", recreate="always") as batch_op:
        batch_op.create_foreign_key(
            "fk_booking_user_id",  # give it a name
            "user",
            ["user_id"],
            ["id"],
            ondelete="CASCADE"
        )


def downgrade():
    with op.batch_alter_table("booking", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_booking_user_id", type_="foreignkey")


    # ### end Alembic commands ###
