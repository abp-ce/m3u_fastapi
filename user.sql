CREATE TABLE m3u_users (
  id NUMBER GENERATED ALWAYS AS IDENTITY,
  name VARCHAR2(30) UNIQUE NOT NULL,
  email VARCHAR2(50) UNIQUE NOT NULL,
  password VARCHAR2(80),
  creation_date TIMESTAMP(0) NOT NULL,
  disabled CHAR(1) CHECK (disabled IN ('Y','N')),
  PRIMARY KEY (id)
);

CREATE TABLE m3u_files (
  id NUMBER GENERATED ALWAYS AS IDENTITY,
  user_id NUMBER,
  file_name VARCHAR2(30),
  FOREIGN KEY (user_id) REFERENCES m3u_users(id)
);
