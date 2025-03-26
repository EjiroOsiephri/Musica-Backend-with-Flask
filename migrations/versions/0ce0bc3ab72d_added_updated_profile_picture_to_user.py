"""Added updated  profile_picture to User

Revision ID: 0ce0bc3ab72d
Revises: 0a22bd751215
Create Date: 2025-03-26 23:29:41.788965

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ce0bc3ab72d'
down_revision = '0a22bd751215'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('playlist', schema=None) as batch_op:
        batch_op.drop_column('profile_picture')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_picture', sa.String(length=256), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('profile_picture')

    with op.batch_alter_table('playlist', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_picture', sa.VARCHAR(length=256), autoincrement=False, nullable=True))

    # ### end Alembic commands ###
