import os
import sys
from pathlib import Path
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.generator.sql_generator import load_env_file

load_env_file()
conn = psycopg2.connect(os.environ["NEONDB_URL"], connect_timeout=8)
conn.set_session(readonly=True)
cur = conn.cursor()

tables = [
    "categories", "customers", "employees", "shippers",
    "suppliers", "products", "orders", "orderdetails"
]

checks = [
    ("INDEXES", """
        SELECT t.relname, i.relname, ix.indisprimary,
               ix.indisunique, pg_get_indexdef(i.oid)
        FROM pg_class t
        JOIN pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_index ix ON ix.indrelid = t.oid
        JOIN pg_class i ON i.oid = ix.indexrelid
        WHERE n.nspname = 'public' AND t.relname = ANY(%s)
        ORDER BY t.relname, i.relname
    """),
    ("ATTACHED SEQUENCES", """
        SELECT tbl.relname, a.attname, seq.relname
        FROM pg_class seq
        JOIN pg_namespace ns ON ns.oid = seq.relnamespace
        JOIN pg_depend d ON d.objid = seq.oid
        JOIN pg_class tbl ON tbl.oid = d.refobjid
        JOIN pg_attribute a ON a.attrelid = tbl.oid
                           AND a.attnum = d.refobjsubid
        WHERE ns.nspname = 'public'
          AND seq.relkind = 'S'
          AND tbl.relname = ANY(%s)
        ORDER BY tbl.relname, a.attname
    """),
    ("DEPENDENT VIEWS", """
        SELECT DISTINCT ref.relname, dep.relname
        FROM pg_depend d
        JOIN pg_rewrite rw ON d.classid = 'pg_rewrite'::regclass
                          AND d.objid = rw.oid
        JOIN pg_class dep ON dep.oid = rw.ev_class
        JOIN pg_class ref ON ref.oid = d.refobjid
        JOIN pg_namespace n ON n.oid = ref.relnamespace
        WHERE n.nspname = 'public'
          AND ref.relname = ANY(%s)
          AND dep.relkind IN ('v', 'm')
        ORDER BY ref.relname, dep.relname
    """),
    ("USER TRIGGERS", """
        SELECT c.relname, t.tgname, pg_get_triggerdef(t.oid)
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relname = ANY(%s)
          AND NOT t.tgisinternal
        ORDER BY c.relname, t.tgname
    """)
]

try:
    for title, query in checks:
        print(f"\n=== {title} ===")
        cur.execute(query, (tables,))
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(row)
        else:
            print("None found")

    print("\nREAD-ONLY PREFLIGHT CHECK COMPLETE")
finally:
    cur.close()
    conn.close()
