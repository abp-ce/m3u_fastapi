CREATE TABLE m3u_users (
  id NUMBER GENERATED ALWAYS AS IDENTITY,
  name VARCHAR(30) UNIQUE NOT NULL,
  email VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(80),
  creation_date TIMESTAMP(0) NOT NULL,
  disabled CHAR(1) CHECK (disabled IN ('Y','N'))
);
