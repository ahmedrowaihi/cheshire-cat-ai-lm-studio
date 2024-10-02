FROM python:3.12-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Copy the rest of your application
COPY . .

EXPOSE 6000

CMD ["uvicorn", "bridge:app", "--host", "0.0.0.0", "--port", "6000", "--log-level", "info"]
