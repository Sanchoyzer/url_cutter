#!/bin/bash


alembic upgrade head

exec gunicorn url_cutter.main:app -b 0.0.0.0:9000 -w 4 -k uvicorn.workers.UvicornWorker
