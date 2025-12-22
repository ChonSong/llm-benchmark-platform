FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml ./

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies (--no-root since we're not packaging the app)
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
