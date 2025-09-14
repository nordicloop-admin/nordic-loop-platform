FROM python:3.11-slim


RUN apt-get update && apt-get install -y \
    build-essential libpq-dev gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

COPY ./entrypoint.sh .

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]


