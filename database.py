import sqlite3
import json
import os
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store.db")
JSON_FALLBACK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store_state.json")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    try:
        with conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    cost REAL NOT NULL DEFAULT 0,
                    price REAL NOT NULL DEFAULT 0,
                    qty REAL NOT NULL DEFAULT 0,
                    alertThreshold REAL DEFAULT 5,
                    updated_at INTEGER
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id TEXT PRIMARY KEY,
                    itemId TEXT,
                    itemName TEXT,
                    qty REAL DEFAULT 0,
                    unitPrice REAL DEFAULT 0,
                    unitCost REAL DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    cost REAL DEFAULT 0,
                    profit REAL DEFAULT 0,
                    paymentMethod TEXT,
                    customer TEXT,
                    timestamp TEXT,
                    raw_data TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT,
                    raw_data TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS credit_tx (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    customer TEXT,
                    itemId TEXT,
                    itemName TEXT,
                    qty REAL DEFAULT 0,
                    unitPrice REAL DEFAULT 0,
                    amount REAL DEFAULT 0,
                    timestamp TEXT,
                    note TEXT,
                    raw_data TEXT
                )
            """)

        # Check if DB is empty and JSON exists, perform auto-migration
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stock")
        stock_count = cur.fetchone()[0]

        if stock_count == 0 and os.path.exists(JSON_FALLBACK):
            try:
                with open(JSON_FALLBACK, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"[DB] Initializing SQLite database from existing {JSON_FALLBACK}...")
                save_full_state(data, skip_backup=True)
                print("[DB] Auto-migration to SQLite complete!")
            except Exception as e:
                print(f"[DB] Warning: Auto-migration error: {e}")
    finally:
        conn.close()

def get_full_state():
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Meta
        cur.execute("SELECT value FROM meta WHERE key = '_updatedAt'")
        row = cur.fetchone()
        updated_at = int(row[0]) if row and row[0] else int(time.time() * 1000)

        # Stock
        cur.execute("SELECT id, name, cost, price, qty, alertThreshold FROM stock ORDER BY name ASC")
        stock = []
        for r in cur.fetchall():
            stock.append({
                "id": r["id"],
                "name": r["name"],
                "cost": float(r["cost"]),
                "price": float(r["price"]),
                "qty": float(r["qty"]),
                "alertThreshold": float(r["alertThreshold"])
            })

        # Sales
        cur.execute("SELECT id, itemId, itemName, qty, unitPrice, unitCost, revenue, cost, profit, paymentMethod, customer, timestamp, raw_data FROM sales ORDER BY id DESC")
        sales = []
        for r in cur.fetchall():
            if r["raw_data"]:
                try:
                    s_obj = json.loads(r["raw_data"])
                    sales.append(s_obj)
                    continue
                except Exception:
                    pass
            sales.append({
                "id": r["id"],
                "itemId": r["itemId"],
                "itemName": r["itemName"],
                "qty": float(r["qty"]),
                "unitPrice": float(r["unitPrice"]),
                "unitCost": float(r["unitCost"]),
                "revenue": float(r["revenue"]),
                "cost": float(r["cost"]),
                "profit": float(r["profit"]),
                "paymentMethod": r["paymentMethod"],
                "customer": r["customer"],
                "timestamp": r["timestamp"]
            })

        # Customers
        cur.execute("SELECT id, name, phone, raw_data FROM customers ORDER BY name ASC")
        customers = []
        for r in cur.fetchall():
            if r["raw_data"]:
                try:
                    c_obj = json.loads(r["raw_data"])
                    customers.append(c_obj)
                    continue
                except Exception:
                    pass
            c_dict = {"id": r["id"], "name": r["name"]}
            if r["phone"]:
                c_dict["phone"] = r["phone"]
            customers.append(c_dict)

        # Credit Transactions
        cur.execute("SELECT id, type, customer, itemId, itemName, qty, unitPrice, amount, timestamp, note, raw_data FROM credit_tx ORDER BY id DESC")
        credit_tx = []
        for r in cur.fetchall():
            if r["raw_data"]:
                try:
                    tx_obj = json.loads(r["raw_data"])
                    credit_tx.append(tx_obj)
                    continue
                except Exception:
                    pass
            credit_tx.append({
                "id": r["id"],
                "type": r["type"],
                "customer": r["customer"],
                "itemId": r["itemId"],
                "itemName": r["itemName"],
                "qty": float(r["qty"]),
                "unitPrice": float(r["unitPrice"]),
                "amount": float(r["amount"]),
                "timestamp": r["timestamp"],
                "note": r["note"]
            })

        return {
            "stock": stock,
            "sales": sales,
            "customers": customers,
            "creditTx": credit_tx,
            "_updatedAt": updated_at
        }
    finally:
        conn.close()

def save_full_state(data, skip_backup=False):
    conn = get_connection()
    try:
        updated_at = data.get("_updatedAt", int(time.time() * 1000))
        stock_list = data.get("stock", [])
        sales_list = data.get("sales", [])
        customers_list = data.get("customers", [])
        credit_tx_list = data.get("creditTx", [])

        with conn:
            # Update meta timestamp
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('_updatedAt', ?)", (str(updated_at),))

            # Stock sync (clear & repopulate or upsert)
            conn.execute("DELETE FROM stock")
            stock_rows = []
            for item in stock_list:
                stock_rows.append((
                    str(item.get("id", "")),
                    str(item.get("name", "")),
                    float(item.get("cost", 0) or 0),
                    float(item.get("price", 0) or 0),
                    float(item.get("qty", 0) or 0),
                    float(item.get("alertThreshold", 5) or 5),
                    int(updated_at)
                ))
            if stock_rows:
                conn.executemany("""
                    INSERT INTO stock (id, name, cost, price, qty, alertThreshold, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, stock_rows)

            # Sales sync
            conn.execute("DELETE FROM sales")
            sales_rows = []
            for s in sales_list:
                sales_rows.append((
                    str(s.get("id", "")),
                    str(s.get("itemId", "")),
                    str(s.get("itemName", "")),
                    float(s.get("qty", 0) or 0),
                    float(s.get("unitPrice", 0) or 0),
                    float(s.get("unitCost", 0) or 0),
                    float(s.get("revenue", 0) or 0),
                    float(s.get("cost", 0) or 0),
                    float(s.get("profit", 0) or 0),
                    str(s.get("paymentMethod", "")),
                    str(s.get("customer", "")),
                    str(s.get("timestamp", "")),
                    json.dumps(s)
                ))
            if sales_rows:
                conn.executemany("""
                    INSERT INTO sales (id, itemId, itemName, qty, unitPrice, unitCost, revenue, cost, profit, paymentMethod, customer, timestamp, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, sales_rows)

            # Customers sync
            conn.execute("DELETE FROM customers")
            cust_rows = []
            for c in customers_list:
                cust_rows.append((
                    str(c.get("id", "")),
                    str(c.get("name", "")),
                    str(c.get("phone", "")),
                    json.dumps(c)
                ))
            if cust_rows:
                conn.executemany("""
                    INSERT INTO customers (id, name, phone, raw_data)
                    VALUES (?, ?, ?, ?)
                """, cust_rows)

            # Credit Tx sync
            conn.execute("DELETE FROM credit_tx")
            tx_rows = []
            for tx in credit_tx_list:
                tx_rows.append((
                    str(tx.get("id", "")),
                    str(tx.get("type", "")),
                    str(tx.get("customer", "")),
                    str(tx.get("itemId", "")),
                    str(tx.get("itemName", "")),
                    float(tx.get("qty", 0) or 0),
                    float(tx.get("unitPrice", 0) or 0),
                    float(tx.get("amount", 0) or 0),
                    str(tx.get("timestamp", "")),
                    str(tx.get("note", "")),
                    json.dumps(tx)
                ))
            if tx_rows:
                conn.executemany("""
                    INSERT INTO credit_tx (id, type, customer, itemId, itemName, qty, unitPrice, amount, timestamp, note, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, tx_rows)

        # Also maintain JSON backup file for safety
        if not skip_backup:
            try:
                with open(JSON_FALLBACK, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"[DB] Backup write error: {e}")

        return True
    finally:
        conn.close()

def get_stats():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), SUM(qty), SUM(qty * cost), SUM(qty * price) FROM stock")
        stk_count, total_units, total_cost_val, total_retail_val = cur.fetchone()

        cur.execute("SELECT COUNT(*), SUM(revenue), SUM(profit) FROM sales")
        sales_count, total_revenue, total_profit = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM customers")
        customer_count = cur.fetchone()[0]

        cur.execute("""
            SELECT 
                SUM(CASE WHEN type = 'CREDIT' THEN amount ELSE 0 END) -
                SUM(CASE WHEN type = 'PAYMENT' THEN amount ELSE 0 END)
            FROM credit_tx
        """)
        outstanding_credit = cur.fetchone()[0]

        db_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0

        return {
            "database": "SQLite 3",
            "file": "store.db",
            "size_kb": round(db_size_bytes / 1024, 2),
            "stock_items_count": stk_count or 0,
            "total_inventory_units": round(total_units or 0, 2),
            "inventory_cost_value": round(total_cost_val or 0, 2),
            "inventory_retail_value": round(total_retail_val or 0, 2),
            "sales_count": sales_count or 0,
            "total_revenue": round(total_revenue or 0, 2),
            "total_profit": round(total_profit or 0, 2),
            "customer_count": customer_count or 0,
            "outstanding_khata_credit": round(outstanding_credit or 0, 2)
        }
    finally:
        conn.close()
