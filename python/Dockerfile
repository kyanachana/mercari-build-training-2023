FROM python:3.10.6-alpine

WORKDIR /app

RUN addgroup -S mercari && adduser -S trainee -G mercari

COPY requirements.txt .

RUN apk add --no-cache curl
RUN pip install -r --no-cache app/python/requirements.txt

COPY . .

USER trainee

CMD ["uvicorn", "main:app","--reload","--port","9000","--host","0.0.0.0"]