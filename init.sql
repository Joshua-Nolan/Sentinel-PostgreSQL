CREATE TABLE logs(
    id SERIAL NOT NULL PRIMARY KEY,
    timestamp TIMESTAMPTZ,
    event_type TEXT,
    source_ip TEXT,
    destination TEXT,
    username TEXT,
    severity TEXT,
    message TEXT,
    log_id TEXT
);