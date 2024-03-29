docker run --name m3u-fastapi -v ~/abp-m3u/populate-epg/wallet:/opt/oracle/instantclient_21_3/network/admin \
    -v ~/abp-m3u/fastapi:/app/app -v ~/abp-m3u/files:/app/files -v ~/.ssh:/secrets -p 8000:80 \
    -e MAX_WORKERS="2" \
    --env-file ~/abp-m3u/fastapi/.env m3u-fastapi
    # -e ATP_USER=$ATP_USER -e ATP_PASSWORD=$ATP_PASSWORD -e ATP_DSN=$ATP_DSN -e TELEBOT=$TELEBOT \
    # -e GUNICORN_CMD_ARGS="--keyfile=/secrets/telegram.key --certfile=/secrets/telegram.pem" m3u-fastapi
    