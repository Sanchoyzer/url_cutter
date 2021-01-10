FROM python:3.8-alpine as base

# builder

FROM base as builder
RUN mkdir /install
WORKDIR /install
RUN apk add --no-cache make gcc python3-dev libffi-dev musl-dev postgresql-dev zlib-dev jpeg-dev openssl-dev cargo \
    && pip3 install --no-cache-dir -U pip wheel setuptools poetry

COPY pyproject.toml poetry.lock README.md ./
COPY ./url_cutter url_cutter
RUN poetry config virtualenvs.create false \
    && poetry build -f wheel -n \
    && poetry export --without-hashes -o requirements.txt \
    && pip3 wheel --wheel-dir=/install/dist -r requirements.txt


# main

FROM base
COPY --from=builder /install/dist /usr/local/wheels

RUN mkdir -p /srv/src/migrations
WORKDIR /srv/src
RUN apk add --no-cache postgresql-libs jpeg-dev \
    && pip3 install --no-cache-dir -U pip wheel setuptools

RUN pip3 install --no-cache-dir --no-index --find-links=/usr/local/wheels/ url_cutter \
    && rm -r /usr/local/wheels
COPY .env alembic.ini entrypoint.sh ./

ENV PYTHONPATH=/srv/src
