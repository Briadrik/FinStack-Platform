"""
 Realistic African Fintech Data Generator
Simulates real-time wallet transactions across 6 African markets
"""

import psycopg2
import random
import time
import uuid
from datetime import datetime, timedelta
from faker import Faker

# ── African locale fakers ──────────────────────────────────────
fake_ke = Faker('en_GB')   # Faker has no sw_KE — en_GB as base
fake_en = Faker('en_GB')
fake    = Faker()

# ── DB Connection ──────────────────────────────────────────────
conn = psycopg2.connect(
    host="127.0.0.1", port=5434,    # 5434 = our mapped port
    dbname="zamupay_db",
    user="zamupay", password="zamupay123"
)
cur = conn.cursor()

# African Names by Country 
NAMES = {
    'KE': [
        "Amina Wanjiru","Brian Otieno","Grace Njeri","David Kamau","Faith Achieng",
        "James Mwangi","Mercy Wanjiku","Peter Ochieng","Susan Wairimu","Tom Kariuki",
        "Cynthia Auma","Kevin Mutua","Diana Chebet","Moses Kipchoge","Agnes Wambui"
    ],
    'NG': [
        "Chukwuemeka Obi","Fatima Bello","Adewale Okafor","Ngozi Adeyemi","Emeka Eze",
        "Aisha Mohammed","Tunde Bakare","Chioma Okonkwo","Segun Adebayo","Yetunde Lawal"
    ],
    'GH': [
        "Kwame Mensah","Abena Owusu","Kofi Asante","Ama Boateng","Kweku Frimpong",
        "Akosua Darko","Yaw Amponsah","Efua Ankrah","Kojo Asare","Adwoa Osei"
    ],
    'ZA': [
        "Thabo Dlamini","Nomvula Nkosi","Sipho Ndlovu","Zanele Khumalo","Bongani Zulu",
        "Lerato Molefe","Lungelo Mthembu","Busisiwe Shabalala","Nhlanhla Mkhize","Palesa Mokoena"
    ],
    'TZ': [
        "Juma Mwamba","Halima Msigwa","Baraka Moshi","Zawadi Kibona","Hassan Mwangi"
    ],
    'UG': [
        "Ronald Ssemakula","Prossy Namukasa","Henry Okello","Immaculate Akello","Robert Byarugaba"
    ]
}

# Phone prefixes by country 
PHONE_PREFIXES = {
    'KE': ['+2547', '+2541'],          # Safaricom, Airtel
    'NG': ['+2348', '+2347'],
    'GH': ['+23324', '+23320'],
    'ZA': ['+2760', '+2782'],
    'TZ': ['+25575', '+25571'],
    'UG': ['+25677', '+25670']
}

PAYMENT_CHANNELS = ['mpesa','airtel_money','bank_transfer','card','ussd','app','agent']
TX_TYPES = [
    'send_money','send_money','send_money',       # most common
    'receive_money','receive_money',
    'bill_payment','bill_payment',
    'merchant_payment','merchant_payment',
    'airtime','airtime',
    'deposit','withdrawal',
    'forex_exchange'
]
STATUSES = (
    ['completed'] * 70 +
    ['failed'] * 10 +
    ['pending'] * 10 +
    ['flagged'] * 10
)
DEVICES = ['mobile', 'mobile', 'mobile', 'ussd', 'web', 'agent_till']
OCCUPATIONS = [
    'Teacher','Small Business Owner','Engineer','Nurse','Driver',
    'Farmer','Student','Trader','Doctor','Civil Servant','Mechanic',
    'Freelancer','Accountant','Police Officer','Chef'
]
FRAUD_SIGNALS = {
    'sim_swap':         "Customer SIM swapped within 24hrs before transaction",
    'account_takeover': "Login from new device + password reset in same session",
    'velocity_breach':  "More than 10 transactions in 1 hour",
    'geo_mismatch':     "Transaction IP country differs from registration country",
    'large_amount':     "Amount exceeds 3x customer's average transaction value",
    'money_mule':       "Account receiving funds from multiple flagged accounts",
    'device_change':    "New device used for first time with high-value transaction",
    'unusual_hours':    "Transaction at 2–4 AM, unusual for this customer"
}

tx_counter  = 1
cust_counter = 1

def zamu_id(country, n):
    return f"ZM-{country}-{str(n).zfill(6)}"

def zamu_ref(n):
    date = datetime.now().strftime('%Y%m%d')
    return f"ZP-{date}-{str(n).zfill(6)}"

def random_phone(country):
    prefix = random.choice(PHONE_PREFIXES[country])
    suffix = ''.join([str(random.randint(0,9)) for _ in range(7)])
    return prefix + suffix

def seed_customers(n=200):
    global cust_counter
    print(f"\n🌍 Seeding {n} Zamu Pay customers across Africa...\n")
    countries = list(NAMES.keys())

    for i in range(n):
        country = random.choice(countries)
        name    = random.choice(NAMES[country])
        kyc     = random.choices(
                    ['verified','pending','failed','suspended'],
                    weights=[70, 20, 7, 3])[0]
        tier    = random.choices([1,2,3], weights=[50,35,15])[0]
        risk    = random.choices(['low','medium','high'], weights=[70,22,8])[0]
        is_agent = random.random() < 0.05    # 5% are agents

        cur.execute("""
            INSERT INTO customers
              (zamu_id, full_name, phone_number, country_code,
               id_type, id_number, kyc_status, kyc_tier,
               gender, occupation, is_agent, risk_rating)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
            RETURNING customer_id
        """, (
            zamu_id(country, cust_counter),
            name,
            random_phone(country),
            country,
            random.choice(['national_id','passport','drivers_license']),
            fake.bothify(text='??######'),
            kyc, tier,
            random.choice(['Male','Female']),
            random.choice(OCCUPATIONS),
            is_agent, risk
        ))
        result = cur.fetchone()
        if result:
            cid = result[0]
            # Create wallets — home currency + USD for some
            cur.execute("""SELECT currency_code FROM markets WHERE country_code=%s""", (country,))
            home_currency = cur.fetchone()[0]
            for currency in [home_currency] + (['USD'] if random.random() < 0.3 else []):
                balance = round(random.uniform(0, 500000), 2)
                cur.execute("""
                    INSERT INTO wallets (customer_id, currency_code, balance, ledger_balance)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                """, (cid, currency, balance, balance))

        cust_counter += 1
        if (i+1) % 50 == 0:
            conn.commit()
            print(f"  ✅ {i+1} customers created...")

    conn.commit()
    print(f"\n✅ {n} customers seeded!\n")


def stream_transactions():
    global tx_counter
    print("💸 Streaming live Zamu Pay transactions... (Ctrl+C to stop)\n")

    # Preload customer and merchant IDs
    cur.execute("SELECT customer_id, country_code, risk_rating FROM customers WHERE kyc_status='verified'")
    customers = cur.fetchall()
    cur.execute("SELECT merchant_id, country_code FROM merchants WHERE is_active=TRUE")
    merchants = cur.fetchall()

    if not customers:
        print("⚠️  No verified customers found. Check seeding.")
        return

    while True:
        cust_id, cust_country, risk = random.choice(customers)
        merch_id, merch_country    = random.choice(merchants)

        tx_type  = random.choice(TX_TYPES)
        channel  = random.choice(PAYMENT_CHANNELS)
        status   = random.choice(STATUSES)
        device   = random.choice(DEVICES)
        amount   = round(random.uniform(50, 150000), 2)

        # Higher amounts for business-type transactions
        if tx_type in ['forex_exchange','bank_transfer']:
            amount = round(random.uniform(10000, 2000000), 2)

        # Get exchange rate to USD
        cur.execute("""
            SELECT currency_code FROM markets WHERE country_code=%s
        """, (cust_country,))
        row = cur.fetchone()
        currency = row[0] if row else 'USD'

        cur.execute("""
            SELECT rate FROM exchange_rates
            WHERE from_currency=%s AND to_currency='USD'
        """, (currency,))
        rate_row = cur.fetchone()
        rate     = rate_row[0] if rate_row else 1.0
        amount_usd = round(float(amount) * float(rate), 2)

        fee = round(amount * 0.015, 2)  # 1.5% fee

        # Simulate IP mismatch for some transactions
        ip_country = cust_country if random.random() > 0.1 else random.choice(['CN','RU','BR','IN'])

        ref = zamu_ref(tx_counter)

        cur.execute("""
            INSERT INTO transactions
              (zamu_ref, customer_id, merchant_id, transaction_type,
               payment_channel, amount, currency_code, amount_usd,
               fee, exchange_rate, sender_country, receiver_country,
               status, device_type, ip_country, completed_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING transaction_id
        """, (
            ref, cust_id, merch_id, tx_type,
            channel, amount, currency, amount_usd,
            fee, rate, cust_country, merch_country,
            status, device, ip_country,
            datetime.now() if status == 'completed' else None
        ))
        tid = cur.fetchone()[0]

        # Generate Fraud Signals 
        should_flag = (
            status == 'flagged' or
            amount_usd > 5000 or
            ip_country != cust_country or
            risk == 'high'
        )

        if should_flag:
            signal_type   = random.choice(list(FRAUD_SIGNALS.keys()))
            signal_detail = FRAUD_SIGNALS[signal_type]
            risk_score    = round(random.uniform(
                55 if status == 'flagged' else 30, 99
            ), 2)
            action = random.choice(['flagged','blocked','review'])

            cur.execute("""
                INSERT INTO fraud_signals
                  (transaction_id, customer_id, risk_score,
                   signal_type, signal_detail, action_taken)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (tid, cust_id, risk_score, signal_type, signal_detail, action))

        conn.commit()

        # ── Console Log ────────────────────────────────────
        icon = {'completed':'✅','failed':'❌','pending':'⏳','flagged':'🚨'}.get(status,'❓')
        print(f"  {icon} [{ref}] {tx_type:<20} {currency} {amount:>12,.2f}  (~${amount_usd:>8,.2f})  {status}  [{cust_country}→{merch_country}]")

        tx_counter += 1
        time.sleep(random.uniform(0.3, 1.5))  # realistic pace


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║         ZAMU DATA ENGINE         ║
    ║   Africa's Real-Time Payments Data   ║
    ╚══════════════════════════════════════╝
    """)
    seed_customers(200)
    stream_transactions()