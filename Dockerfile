# syntax=docker/dockerfile:1
FROM python:3.12-slim

# copied from https://docs.docker.com/language/python/containerize/
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser
RUN chown appuser /app

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

USER appuser
EXPOSE 8080
# --- end copied parts

STOPSIGNAL SIGINT

COPY ./app ./app
CMD ["python", "app.py"]
