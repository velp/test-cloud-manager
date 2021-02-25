FROM python:3.9.2-buster
COPY rest_api.py core.py requirements.txt /opt/rest_api/
RUN pip install -r /opt/rest_api/requirements.txt
CMD python /opt/rest_api/rest_api.py
