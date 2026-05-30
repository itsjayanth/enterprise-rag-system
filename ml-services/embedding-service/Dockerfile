FROM python:3.11-slim

WORKDIR /app

COPY req.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

COPY ml-services/embedding-service/app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

