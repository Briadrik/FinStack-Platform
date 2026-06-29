-- ============================================================
-- ZAMU PAY Core Database Schema
-- ============================================================

CREATE TABLE markets (
    market_id     SERIAL PRIMARY KEY,
    country_code  VARCHAR(3) UNIQUE NOT NULL,
    country_name  VARCHAR(50),
    currency_code VARCHAR(5),
    is_active     BOOLEAN DEFAULT TRUE
);

INSERT INTO markets (country_code, country_name, currency_code) VALUES
  ('KE', 'Kenya',         'KES'),
  ('NG', 'Nigeria',       'NGN'),
  ('GH', 'Ghana',         'GHS'),
  ('ZA', 'South Africa',  'ZAR'),
  ('TZ', 'Tanzania',      'TZS'),
  ('UG', 'Uganda',        'UGX'),
  ('US', 'United States', 'USD'),
  ('GB', 'United Kingdom','GBP');

CREATE TABLE customers (
    customer_id     SERIAL PRIMARY KEY,
    zamu_id         VARCHAR(12) UNIQUE NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    phone_number    VARCHAR(20) UNIQUE NOT NULL,
    email           VARCHAR(100),
    country_code    VARCHAR(3) REFERENCES markets(country_code),
    id_type         VARCHAR(20),
    id_number       VARCHAR(30),
    kyc_status      VARCHAR(20) DEFAULT 'pending',
    kyc_tier        INT DEFAULT 1,
    date_of_birth   DATE,
    gender          VARCHAR(10),
    occupation      VARCHAR(50),
    is_agent        BOOLEAN DEFAULT FALSE,
    risk_rating     VARCHAR(10) DEFAULT 'low',
    registered_at   TIMESTAMP DEFAULT NOW(),
    last_active_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE wallets (
    wallet_id       SERIAL PRIMARY KEY,
    customer_id     INT REFERENCES customers(customer_id),
    currency_code   VARCHAR(5),
    balance         DECIMAL(15,2) DEFAULT 0.00,
    ledger_balance  DECIMAL(15,2) DEFAULT 0.00,
    wallet_status   VARCHAR(20) DEFAULT 'active',
    daily_limit     DECIMAL(15,2) DEFAULT 300000,
    monthly_limit   DECIMAL(15,2) DEFAULT 5000000,
    created_at      TIMESTAMP DEFAULT NOW(),
    last_updated    TIMESTAMP DEFAULT NOW(),
    UNIQUE(customer_id, currency_code)
);

CREATE TABLE merchants (
    merchant_id     SERIAL PRIMARY KEY,
    merchant_name   VARCHAR(100) NOT NULL,
    category        VARCHAR(50),
    country_code    VARCHAR(3) REFERENCES markets(country_code),
    is_active       BOOLEAN DEFAULT TRUE
);

INSERT INTO merchants (merchant_name, category, country_code) VALUES
  ('Safaricom M-Pesa',   'telco',         'KE'),
  ('Airtel Money Kenya', 'telco',         'KE'),
  ('KPLC',               'utilities',     'KE'),
  ('Nairobi Water',      'utilities',     'KE'),
  ('Jumia Kenya',        'ecommerce',     'KE'),
  ('Bolt Kenya',         'transport',     'KE'),
  ('Uber Kenya',         'transport',     'KE'),
  ('Java House',         'food',          'KE'),
  ('KFC Kenya',          'food',          'KE'),
  ('DStv Kenya',         'entertainment', 'KE'),
  ('Showmax',            'entertainment', 'KE'),
  ('MTN Mobile Money',   'telco',         'NG'),
  ('Opay Nigeria',       'fintech',       'NG'),
  ('Jumia Nigeria',      'ecommerce',     'NG'),
  ('DStv Nigeria',       'entertainment', 'NG'),
  ('MTN Ghana',          'telco',         'GH'),
  ('Vodafone Cash',      'telco',         'GH'),
  ('Capitec Bank',       'banking',       'ZA'),
  ('Takealot',           'ecommerce',     'ZA'),
  ('Vodacom Tanzania',   'telco',         'TZ'),
  ('Airtel Uganda',      'telco',         'UG'),
  ('Amazon',             'ecommerce',     'US'),
  ('Netflix',            'entertainment', 'US'),
  ('Spotify',            'entertainment', 'US'),
  ('Flutterwave',        'fintech',       'NG');

CREATE TABLE transactions (
    transaction_id      SERIAL PRIMARY KEY,
    zamu_ref            VARCHAR(20) UNIQUE NOT NULL,
    customer_id         INT REFERENCES customers(customer_id),
    merchant_id         INT REFERENCES merchants(merchant_id),
    transaction_type    VARCHAR(30) NOT NULL,
    payment_channel     VARCHAR(30),
    amount              DECIMAL(15,2) NOT NULL,
    currency_code       VARCHAR(5),
    amount_usd          DECIMAL(15,2),
    fee                 DECIMAL(10,2) DEFAULT 0.00,
    exchange_rate       DECIMAL(12,6),
    sender_country      VARCHAR(3) REFERENCES markets(country_code),
    receiver_country    VARCHAR(3) REFERENCES markets(country_code),
    status              VARCHAR(20) DEFAULT 'pending',
    failure_reason      VARCHAR(100),
    device_type         VARCHAR(20),
    ip_address          VARCHAR(45),
    ip_country          VARCHAR(3),
    created_at          TIMESTAMP DEFAULT NOW(),
    completed_at        TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fraud_signals (
    signal_id           SERIAL PRIMARY KEY,
    transaction_id      INT REFERENCES transactions(transaction_id),
    customer_id         INT REFERENCES customers(customer_id),
    risk_score          DECIMAL(5,2),
    signal_type         VARCHAR(50),
    signal_detail       TEXT,
    action_taken        VARCHAR(30) DEFAULT 'flagged',
    reviewed_by         VARCHAR(50),
    resolved            BOOLEAN DEFAULT FALSE,
    flagged_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE exchange_rates (
    rate_id         SERIAL PRIMARY KEY,
    from_currency   VARCHAR(5),
    to_currency     VARCHAR(5),
    rate            DECIMAL(15,6),
    recorded_at     TIMESTAMP DEFAULT NOW()
);

INSERT INTO exchange_rates (from_currency, to_currency, rate) VALUES
  ('KES', 'USD', 0.00775),
  ('NGN', 'USD', 0.00063),
  ('GHS', 'USD', 0.06800),
  ('ZAR', 'USD', 0.05400),
  ('TZS', 'USD', 0.00039),
  ('UGX', 'USD', 0.00027),
  ('USD', 'KES', 129.00),
  ('USD', 'NGN', 1580.00),
  ('GBP', 'USD', 1.27000);

CREATE INDEX idx_transactions_customer   ON transactions(customer_id);
CREATE INDEX idx_transactions_status     ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_type       ON transactions(transaction_type);
CREATE INDEX idx_fraud_customer          ON fraud_signals(customer_id);
CREATE INDEX idx_fraud_score             ON fraud_signals(risk_score);
CREATE INDEX idx_customers_country       ON customers(country_code);
CREATE INDEX idx_customers_kyc           ON customers(kyc_status);
