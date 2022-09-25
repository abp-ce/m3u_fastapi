docker run --name psql -v pg_data:/var/lib/postgresql/data -e POSTGRES_USER=m3u \
    -e POSTGRES_PASSWORD=asdrty68 -p 5432:5432 -d --restart always postgres:alpine
