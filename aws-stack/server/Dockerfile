FROM python:3.12-slim AS build

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential

COPY ./app /app
COPY ./requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get install -y curl gnupg && \
    curl -fsSL https://playwright.dev/python/docs/installation-script/ | python - 
# && \
# playwright install --with-deps chromium

FROM python:3.12-slim

WORKDIR /app

COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /app /app
# COPY --from=build /root/.cache /root/.cache

ENV PLAYWRIGHT_BROWSERS_PATH=/var/task/bin

RUN playwright install-deps
RUN playwright install chromium


# COPY .env /app

EXPOSE 8000

CMD ["uvicorn", "chainlit_main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "backend"]