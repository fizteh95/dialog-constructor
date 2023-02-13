FROM python:3.11.2-alpine3.16

COPY requirements.txt /tmp/
# git sqlite3 libpq-dev libpq5 gcc g++
RUN apk update && apk add bash
RUN apk add gcc g++
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /src
COPY src/ /src/src/
COPY main.py alembic.ini setup.cfg /src/
COPY tests/ /tests/

# RUN mkdir -p /fake
COPY fake_isfront/isfront.py /src/

WORKDIR /src

EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=5s --retries=5 --start-period=5s CMD curl -f 0.0.0.0:8080/healthcheck || exit 1
# CMD python main.py
