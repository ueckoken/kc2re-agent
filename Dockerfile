FROM python:3.9

RUN pip install poetry

WORKDIR /app
COPY pyproject.toml ./
RUN poetry install
COPY . .

CMD poetry run python serve.py