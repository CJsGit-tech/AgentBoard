FROM node:22-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
RUN mkdir -p /srv/app /var/lib/agentboard-executor /run/agentboard-executor
COPY app/executor.py /srv/app/executor.py
RUN touch /srv/app/__init__.py && chmod 0555 /srv/app /srv/app/executor.py
USER 0:0
ENTRYPOINT ["python3", "-m", "app.executor"]
