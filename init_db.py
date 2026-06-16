import sqlite3

def initialize_database():
    # Connect to SQLite database (It will create 'french_retail.db' automatically)
    conn = sqlite3.connect("french_retail.db")
    cursor = conn.cursor()

    # 1. Create the Orders Table (For Refund Agent)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        amount REAL NOT NULL,
        days_passed INTEGER NOT NULL
    )
    """)

    # 2. Create the FAQ Store Table (For QA Agent)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faq_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT UNIQUE NOT NULL,
        response_text TEXT NOT NULL
    )
    """)

    # 3. Insert Dummy Data into Orders
    orders_data = [
        ("FR-10243", "Anand", 150.00, 12),     # Within 30 days -> Approved
        ("FR-99821", "John", 89.99, 45),       # Out of 30 days -> Rejected
        ("FR-55421", "Sarah", 230.50, 5)       # Within 30 days -> Approved
    ]
    
    cursor.executemany("""
    INSERT OR REPLACE INTO orders (order_id, customer_name, amount, days_passed)
    VALUES (?, ?, ?, ?)
    """, orders_data)

    # 4. Insert Dummy Data into FAQ Store (Keywords that LLM can match)
    faq_data = [
        ("hours", "Our flagship store is open Monday to Saturday from 9 AM to 8 PM. We are closed on Sundays."),
        ("location", "Our premium flagship boutique is located at 75 Avenue des Champs-Élysées, Paris, France."),
        ("shipping", "Standard shipping takes 3-5 business days within Europe. Express shipping options are available at checkout."),
        ("contact", "You can reach our customer helpline at +33 1 23 45 67 89 or email us at support@frenchretail.com."),
        ("details", "Welcome to French Retail! Our premium flagship boutique is located at 75 Avenue des Champs-Élysées, Paris, France. We are open Mon-Sat, 9 AM to 8 PM.")
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO faq_store (keyword, response_text)
    VALUES (?, ?)
    """, faq_data)

    # Commit changes and close
    conn.commit()
    conn.close()
    print("🎯 Success: 'french_retail.db' created with 'orders' and 'faq_store' tables filled!")

if __name__ == "__main__":
    initialize_database()