def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            type VARCHAR(20) NOT NULL,
            amount NUMERIC(15,2) NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Eski Boshqa kategoriyasidagi bozor xarajatlarini
    # 🛒 Bozor kategoriyasiga o'tkazish
    cur.execute("""
        UPDATE transactions
        SET category = '🛒 Bozor'
        WHERE type = 'expense'
          AND category = '📦 Boshqa'
          AND (
              LOWER(description) LIKE '%bozor%'
              OR LOWER(description) LIKE '%do''kon%'
              OR LOWER(description) LIKE '%dokon%'
              OR LOWER(description) LIKE '%do‘kon%'
              OR LOWER(description) LIKE '%do’kon%'
              OR LOWER(description) LIKE '%suv%'
              OR LOWER(description) LIKE '%non%'
              OR LOWER(description) LIKE '%go''sht%'
              OR LOWER(description) LIKE '%gosht%'
              OR LOWER(description) LIKE '%tovuq%'
              OR LOWER(description) LIKE '%baliq%'
              OR LOWER(description) LIKE '%sut%'
              OR LOWER(description) LIKE '%qatiq%'
              OR LOWER(description) LIKE '%pishloq%'
              OR LOWER(description) LIKE '%tuxum%'
              OR LOWER(description) LIKE '%guruch%'
              OR LOWER(description) LIKE '%makaron%'
              OR LOWER(description) LIKE '%un%'
              OR LOWER(description) LIKE '%shakar%'
              OR LOWER(description) LIKE '%tuz%'
              OR LOWER(description) LIKE '%moy%'
              OR LOWER(description) LIKE '%kartoshka%'
              OR LOWER(description) LIKE '%piyoz%'
              OR LOWER(description) LIKE '%sabzi%'
              OR LOWER(description) LIKE '%pomidor%'
              OR LOWER(description) LIKE '%bodring%'
              OR LOWER(description) LIKE '%sabzavot%'
              OR LOWER(description) LIKE '%meva%'
              OR LOWER(description) LIKE '%olma%'
              OR LOWER(description) LIKE '%banan%'
              OR LOWER(description) LIKE '%uzum%'
              OR LOWER(description) LIKE '%apelsin%'
              OR LOWER(description) LIKE '%mandarin%'
              OR LOWER(description) LIKE '%limon%'
              OR LOWER(description) LIKE '%tarvuz%'
              OR LOWER(description) LIKE '%qovun%'
              OR LOWER(description) LIKE '%shokolad%'
              OR LOWER(description) LIKE '%pechenye%'
              OR LOWER(description) LIKE '%konfet%'
              OR LOWER(description) LIKE '%kolbasa%'
              OR LOWER(description) LIKE '%sosiska%'
          )
          AND LOWER(description) NOT LIKE '%suv to%'
    """)

    conn.commit()

    cur.close()
    conn.close()

    print("✅ Eski bozor xarajatlari 🛒 Bozorga o'tkazildi")