FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=contracts . ./contracts
COPY --from=infra backend-entrypoint.sh /usr/local/bin/agentboard-entrypoint
RUN chmod 755 /usr/local/bin/agentboard-entrypoint
ENTRYPOINT ["agentboard-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
