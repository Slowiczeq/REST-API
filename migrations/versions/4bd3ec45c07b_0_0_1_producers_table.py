"""producers table

Revision ID: 4bd3ec45c07b
Revises: 
Create Date: 2021-07-17 02:03:55.575333

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4bd3ec45c07b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('producers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_name', sa.String(length=50), nullable=False),
    sa.Column('headquarters', sa.String(length=50), nullable=False),
    sa.Column('creation_date', sa.Date(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('producers')
    # ### end Alembic commands ###
