FROM python:3.11.7-slim

WORKDIR /app

COPY bridge.py .

EXPOSE 6000

CMD ["python", "bridge.py"]
