FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY kinopoisk_rec_sys kinopoisk_rec_sys
ENTRYPOINT ["fastapi", "run", "kinopoisk_rec_sys/search.py", "--proxy-headers", "--port", "8000"]