FROM python:3

WORKDIR /app

COPY ./ ./

RUN pip install -r requirements.txt && python setup.py sdist && pip install dist/monitor-exporter-0.1.0.tar.gz

CMD [ "python", "-m", "monitor_exporter", "-f", "config.yml" ]
