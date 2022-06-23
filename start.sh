docker run --name m3u-fastapi -v ~/.wallet:/opt/oracle/instantclient_21_3/network/admin \
    -v ~/m3u_fastapi:/app/app -v ~/files:/app/files -p 8000:80 \
    -v ~/db:/app/db -e MAX_WORKERS="2" \
    --env-file ~/m3u_fastapi/.env -d --restart always abpdock/m3u-fastapi
