# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""empty message

Revision ID: 7ce9d96b7f7d
Revises: 45ad11226fc2
Create Date: 2020-01-06 19:22:56.538319

"""

# revision identifiers, used by Alembic.
revision = '7ce9d96b7f7d'
down_revision = '45ad11226fc2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('iou_tables',
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('changed_on', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('default_endpoint', sa.Text(), nullable=True),
    sa.Column('is_featured', sa.Boolean(), nullable=True),
    sa.Column('filter_select_enabled', sa.Boolean(), nullable=True),
    sa.Column('offset', sa.Integer(), nullable=True),
    sa.Column('cache_timeout', sa.Integer(), nullable=True),
    sa.Column('params', sa.String(length=1000), nullable=True),
    sa.Column('perm', sa.String(length=1000), nullable=True),
    sa.Column('table_name', sa.String(length=250), nullable=False),
    sa.Column('main_dttm_col', sa.String(length=250), nullable=True),
    sa.Column('database_id', sa.Integer(), nullable=False),
    sa.Column('fetch_values_predicate', sa.String(length=1000), nullable=True),
    sa.Column('schema', sa.String(length=255), nullable=True),
    sa.Column('sql', sa.Text(), nullable=True),
    sa.Column('is_sqllab_view', sa.Boolean(), nullable=True),
    sa.Column('template_params', sa.Text(), nullable=True),
    sa.Column('created_by_fk', sa.Integer(), nullable=True),
    sa.Column('changed_by_fk', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by_fk'], ['ab_user.id'], ),
    sa.ForeignKeyConstraint(['created_by_fk'], ['ab_user.id'], ),
    sa.ForeignKeyConstraint(['database_id'], ['dbs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('database_id', 'table_name')
    )
    op.create_table('IouTable_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('table_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['table_id'], ['iou_tables.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['ab_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('iou_table_columns',
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('changed_on', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('column_name', sa.String(length=255), nullable=False),
    sa.Column('verbose_name', sa.String(length=1024), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('type', sa.String(length=32), nullable=True),
    sa.Column('groupby', sa.Boolean(), nullable=True),
    sa.Column('filterable', sa.Boolean(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('table_id', sa.Integer(), nullable=True),
    sa.Column('is_dttm', sa.Boolean(), nullable=True),
    sa.Column('expression', sa.Text(), nullable=True),
    sa.Column('python_date_format', sa.String(length=255), nullable=True),
    sa.Column('created_by_fk', sa.Integer(), nullable=True),
    sa.Column('changed_by_fk', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['changed_by_fk'], ['ab_user.id'], ),
    sa.ForeignKeyConstraint(['created_by_fk'], ['ab_user.id'], ),
    sa.ForeignKeyConstraint(['table_id'], ['iou_tables.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('table_id', 'column_name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('iou_table_columns')
    op.drop_table('IouTable_user')
    op.drop_table('iou_tables')
    # ### end Alembic commands ###