FROM python:3

RUN mkdir -p /opt/src/applications
WORKDIR /opt/src/applications

COPY storekeeper/main.py storekeeperMain.py
COPY configuration.py configuration.py
COPY models.py models.py
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "storekeeperMain.py"]