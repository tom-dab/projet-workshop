import psycopg
conn = psycopg.connect(host='127.0.0.1', port=5432, dbname='epsi', user='postgres', password='postgres', autocommit=True)
with conn, conn.cursor() as cur:
    cur.execute("CREATE TABLE IF NOT EXISTS chat_message (id BIGSERIAL PRIMARY KEY, client_id TEXT NOT NULL, text TEXT NOT NULL, is_file BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    cur.execute("INSERT INTO chat_message (client_id, text, is_file) VALUES (%s,%s,%s)", ("seed-client","Message via 127.0.0.1", False))
print("DB_INSERT_OK")
