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

Revision ID: 45ad11226fc2
Revises: 1495eb914ad3
Create Date: 2020-01-06 19:16:29.745904

"""

# revision identifiers, used by Alembic.
revision = '45ad11226fc2'
down_revision = '1495eb914ad3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('annotation', 'layer_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.create_foreign_key(None, 'datasources', 'ab_user', ['changed_by_fk'], ['id'])
    op.alter_column('dbs', 'allow_csv_upload',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('true'))
    op.drop_constraint('_customer_location_uc', 'tables', type_='unique')
    op.create_unique_constraint(None, 'tables', ['database_id', 'table_name'])
    op.drop_index('ix_tagged_object_object_id', table_name='tagged_object')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_tagged_object_object_id', 'tagged_object', ['object_id'], unique=False)
    op.drop_constraint(None, 'tables', type_='unique')
    op.create_unique_constraint('_customer_location_uc', 'tables', ['database_id', 'schema', 'table_name'])
    op.alter_column('dbs', 'allow_csv_upload',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('true'))
    op.drop_constraint(None, 'datasources', type_='foreignkey')
    op.alter_column('annotation', 'layer_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###