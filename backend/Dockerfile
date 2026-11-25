FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --system --create-home agentboard
COPY app app
COPY migrations migrations
USER agentboard
CMD ["uvicorn","app.api:app","--host","0.0.0.0","--port","8000"]
COPY sample sample
COPY tests tests
