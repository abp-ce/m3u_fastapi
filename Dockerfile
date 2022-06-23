FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
RUN apt update && apt install -y libaio1
COPY ./requirements.txt /app/requirements.txt
COPY ./prestart.sh /app/prestart.sh
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN wget -P /root https://download.oracle.com/otn_software/linux/instantclient/213000/instantclient-basiclite-linux.x64-21.3.0.0.0.zip
WORKDIR /opt/oracle
RUN unzip /root/instantclient-basiclite-linux.x64-21.3.0.0.0.zip
#COPY wallet/* /opt/oracle/instantclient_21_3/network/admin/
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_3:$LD_LIBRARY_PATH
#WORKDIR /root
RUN rm /root/instantclient-basiclite-linux.x64-21.3.0.0.0.zip
WORKDIR /app/app
#COPY ./app /app