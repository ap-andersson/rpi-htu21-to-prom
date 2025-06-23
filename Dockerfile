FROM python:3.11-bookworm

RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir \
    requests \
    prometheus_client \
    adafruit-circuitpython-htu21d \
    RPi.GPIO \
    lgpio

COPY main.py .

EXPOSE 8000

CMD ["python3", "-u", "main.py"]
