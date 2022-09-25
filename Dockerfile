# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
FROM python:3.9
RUN apt update
# RUN apt install -y python3.9-dev 
# RUN apt update && apt install -y libaio1
COPY ./requirements.txt /app/requirements.txt
# COPY ./prestart.sh /app/prestart.sh
RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN pip uninstall psycopg2-binary
RUN pip install --no-cache-dir --upgrade psycopg2
# RUN wget -P /root https://download.oracle.com/otn_software/linux/instantclient/213000/instantclient-basiclite-linux.x64-21.3.0.0.0.zip
# WORKDIR /opt/oracle
# RUN unzip /root/instantclient-basiclite-linux.x64-21.3.0.0.0.zip
#COPY wallet/* /opt/oracle/instantclient_21_3/network/admin/
# ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_3:$LD_LIBRARY_PATH
#WORKDIR /root
# RUN rm /root/instantclient-basiclite-linux.x64-21.3.0.0.0.zip
WORKDIR /app/app
# COPY . ./
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--ssl-keyfile", "/secrets/telegram.key", "--ssl-certfile", "/secrets/telegram.pem"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--proxy-headers"]