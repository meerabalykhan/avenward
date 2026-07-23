FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
RUN python -m pip install --prefix=/install .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/avenward/.local/bin:${PATH}"

RUN groupadd --system avenward \
    && useradd --system --gid avenward --create-home avenward

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=avenward:avenward app ./app
COPY --from=builder --chown=avenward:avenward /build/alembic.ini ./
COPY --from=builder --chown=avenward:avenward /build/migrations ./migrations

USER avenward
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log"]
