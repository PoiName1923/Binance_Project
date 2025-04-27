CREATE TABLE IF NOT EXISTS kline_data (
    symbol VARCHAR(20),
    open_time BIGINT,
    close_time BIGINT,
    interval VARCHAR(10),
    open_price DOUBLE PRECISION,
    close_price DOUBLE PRECISION,
    high_price DOUBLE PRECISION,
    low_price DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    quote_volume DOUBLE PRECISION,
    number_of_trades INTEGER,
    is_closed BOOLEAN,
    processing_time TIMESTAMP,
    open_timestamp TIMESTAMP,
    close_timestamp TIMESTAMP,
    date DATE,
    volatility DOUBLE PRECISION,
    price_change_pct DOUBLE PRECISION,
    trend VARCHAR(10),
    PRIMARY KEY (symbol, open_time)
);

-- Tạo index trên các cột thường dùng để filter
CREATE INDEX IF NOT EXISTS idx_kline_symbol ON kline_data (symbol);
CREATE INDEX IF NOT EXISTS idx_kline_open_time ON kline_data (open_time);
CREATE INDEX IF NOT EXISTS idx_kline_processing_time ON kline_data (processing_time);