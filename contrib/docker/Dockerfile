#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
FROM python:3.6-jessie

RUN useradd --user-group  --no-log-init --shell /bin/bash superset

# Configure environment
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update -y

# Install dependencies to fix `curl https support error` and `elaying package configuration warning`
RUN apt-get install -y apt-transport-https apt-utils

# Install superset dependencies
# https://superset.incubator.apache.org/installation.html#os-dependencies
RUN apt-get install -y build-essential libssl-dev \
    libffi-dev python3-dev libsasl2-dev libldap2-dev libxi-dev

# Install extra useful tool for development
RUN apt-get install -y vim less postgresql-client redis-tools

RUN apt-get install curl gnupg -yq \
    && curl -sL https://deb.nodesource.com/setup_10.x | bash \
    && apt-get install nodejs -yq --force-yes \
    && apt-get -yq install gconf-service libasound2 libatk1.0-0 libc6 libcairo2 \
    libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 \
    libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 \
    libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 \
    libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget libgbm-dev


WORKDIR /root/

COPY requirements.txt .
COPY requirements-dev.txt .
COPY contrib/docker/requirements-extra.txt .
COPY build_docker.sh .

RUN pip install --upgrade setuptools pip \
    && pip install Cython \
    && pip install -r requirements.txt -r requirements-dev.txt -r requirements-extra.txt \
    && rm -rf /root/.cache/pip

RUN  mkdir /var/docker_superset

COPY --chown=superset:superset superset /var/docker_superset/superset
COPY contrib/docker/docker-entrypoint.sh /var/docker_superset/entrypoint.sh

RUN cd /var/docker_superset/ && bash /root/build_docker.sh --inplace

ENV PATH=/var/docker_superset/superset/bin:$PATH \
    PYTHONPATH=/var/docker_superset/superset/:$PYTHONPATH \
    FLASK_APP=/var/docker_superset/superset:app

RUN npm install puppeteer config yargs \
    && mv node_modules/ /var/docker_superset/superset/assets/node_modules/

USER superset

RUN mkdir /var/docker_superset/superset/static/reports

#Run npm -i locally
#RUN cd superset/assets \
#    && npm ci \
#    && npm run build \
#    && rm -rf node_modules


#ENTRYPOINT ["gunicorn", "--bind 0.0.0.0:8088", "--workers $((2 * $(getconf _NPROCESSORS_ONLN) + 1))", "--timeout 60", "--limit-request-line 0", "--limit-request-field_size 0", "superset:app"]
ENTRYPOINT ["/var/docker_superset/entrypoint.sh"]
HEALTHCHECK CMD ["curl", "-f", "http://localhost:8088/health"]

EXPOSE 8088
