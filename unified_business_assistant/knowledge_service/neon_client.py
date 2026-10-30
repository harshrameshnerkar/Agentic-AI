import hashlib
import os
from typing import Any
import requests
from dotenv import load_dotenv

load_dotenv()
parent_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(parent_env):
    load_dotenv(parent_env)


class NeonDBClient:
    def __init__(self, connection_url: str | None = None):
        self.conn_str = connection_url or os.getenv("DATABASE_URL")
        if not self.conn_str:
            raise ValueError("DATABASE_URL is not set in .env")

        parts = self.conn_str.split("@")
        if len(parts) > 1:
            host_and_rest = parts[1].split("/")[0]
            host = host_and_rest.split("?")[0].replace("-pooler", "")
            self.http_url = f"https://{host}/sql"
        else:
            raise ValueError("Invalid DATABASE_URL format.")

        self.headers = {
            "Neon-Connection-String": self.conn_str.replace("-pooler", ""),
            "Content-Type": "application/json",
        }

    def execute_query(self, sql: str, params: list[Any] | None = None):
        payload: dict[str, Any] = {"query": sql}
        if params:
            payload["params"] = params

        response = requests.post(self.http_url, headers=self.headers, json=payload, timeout=20)
        if response.status_code != 200:
            raise RuntimeError(f"Neon SQL Error ({response.status_code}): {response.text}")
        return response.json()

    def test_connection(self):
        res = self.execute_query("SELECT current_database(), current_user, version();")
        rows = res.get("rows", [])
        if rows:
            return {
                "connected": True,
                "database": rows[0].get("current_database"),
                "user": rows[0].get("current_user"),
                "version": rows[0].get("version"),
            }
        return {"connected": False}

    def create_table_if_not_exists(self):
        table_ddl = """
        CREATE TABLE IF NOT EXISTS rag_documents (
            sr_no SERIAL PRIMARY KEY,
            chunk_id VARCHAR(100) UNIQUE NOT NULL,
            chunk_text TEXT NOT NULL,
            source_name VARCHAR(255) NOT NULL,
            page_number INT NOT NULL,
            score_confidence FLOAT DEFAULT NULL,
            embedding_model VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.execute_query(table_ddl)
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_rag_docs_source ON rag_documents(source_name);")
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_rag_docs_chunk_id ON rag_documents(chunk_id);")

        chat_ddl = """
        CREATE TABLE IF NOT EXISTS rag_chat_logs (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100) NOT NULL,
            user_query TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            sources_cited TEXT DEFAULT '',
            confidence_score FLOAT DEFAULT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.execute_query(chat_ddl)
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_chat_session ON rag_chat_logs(session_id);")
        return True

    def log_chat_interaction(self, session_id: str, query: str, response: str, sources: str = "", score: float | None = None):
        try:
            s_id = str(session_id).replace("'", "''")
            q = str(query).replace("\x00", "").replace("'", "''")
            r = str(response).replace("\x00", "").replace("'", "''")
            src = str(sources).replace("'", "''")
            sc_str = f"{score}" if score is not None else "NULL"
            sql = f"""
            INSERT INTO rag_chat_logs (session_id, user_query, bot_response, sources_cited, confidence_score)
            VALUES ('{s_id}', '{q}', '{r}', '{src}', {sc_str});
            """
            self.execute_query(sql)
            return True
        except Exception as e:
            print(f"Warning: Could not log chat to Neon: {e}")
            return False

    def get_chat_history(self, session_id: str, limit: int = 6):
        try:
            s_id = str(session_id).replace("'", "''")
            sql = f"""
            SELECT user_query, bot_response, created_at
            FROM rag_chat_logs
            WHERE session_id = '{s_id}'
            ORDER BY created_at DESC
            LIMIT {limit};
            """
            res = self.execute_query(sql)
            return list(reversed(res.get("rows", [])))
        except Exception:
            return []

    def get_existing_chunk_ids(self) -> set:
        try:
            res = self.execute_query("SELECT chunk_id FROM rag_documents;")
            return {r["chunk_id"] for r in res.get("rows", []) if "chunk_id" in r}
        except Exception:
            return set()

    def resequence_serial_numbers(self):
        try:
            sql = """
            WITH renumbered AS (
                SELECT chunk_id, ROW_NUMBER() OVER (ORDER BY source_name ASC, page_number ASC, chunk_id ASC) AS new_sr
                FROM rag_documents
            )
            UPDATE rag_documents
            SET sr_no = renumbered.new_sr
            FROM renumbered
            WHERE rag_documents.chunk_id = renumbered.chunk_id;
            """
            self.execute_query(sql)
            self.execute_query("""
                SELECT setval(
                    pg_get_serial_sequence('rag_documents', 'sr_no'),
                    COALESCE((SELECT MAX(sr_no) FROM rag_documents), 1)
                );
            """)
            return True
        except Exception as e:
            print(f"Warning: Could not resequence serial numbers: {e}")
            return False

    def insert_chunks(self, chunks: list, embedding_model_name: str = "all-MiniLM-L6-v2", batch_size: int = 50):
        self.create_table_if_not_exists()
        existing_ids = self.get_existing_chunk_ids()
        new_chunks = [ch for ch in chunks if ch["chunk_id"] not in existing_ids]

        if not new_chunks:
            return 0

        res_max = self.execute_query("SELECT COALESCE(MAX(sr_no), 0) AS max_sr FROM rag_documents;")
        current_sr = int(res_max.get("rows", [{}])[0].get("max_sr", 0))
        inserted_count = 0

        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i : i + batch_size]
            values_clauses = []

            for item in batch:
                current_sr += 1
                c_id = str(item["chunk_id"]).replace("'", "''")
                raw_text = str(item["text"]).replace("\x00", "").replace("\u0000", "")
                c_text = raw_text.replace("'", "''")
                s_name = str(item["source"]).replace("'", "''")
                page_no = int(item.get("page", 1))
                score = item.get("score")
                score_str = f"{score}" if score is not None else "NULL"
                model_name = str(embedding_model_name).replace("'", "''")

                values_clauses.append(
                    f"({current_sr}, '{c_id}', '{c_text}', '{s_name}', {page_no}, {score_str}, '{model_name}')"
                )

            if not values_clauses:
                continue

            sql = f"""
            INSERT INTO rag_documents (sr_no, chunk_id, chunk_text, source_name, page_number, score_confidence, embedding_model)
            VALUES {", ".join(values_clauses)}
            ON CONFLICT (chunk_id) DO NOTHING;
            """
            try:
                self.execute_query(sql)
                inserted_count += len(batch)
            except Exception:
                for item in batch:
                    try:
                        c_id = str(item["chunk_id"]).replace("'", "''")
                        c_text = str(item["text"]).replace("\x00", "").replace("\u0000", "").replace("'", "''")
                        s_name = str(item["source"]).replace("'", "''")
                        page_no = int(item.get("page", 1))
                        model_name = str(embedding_model_name).replace("'", "''")
                        single_sql = f"""
                        INSERT INTO rag_documents (chunk_id, chunk_text, source_name, page_number, score_confidence, embedding_model)
                        VALUES ('{c_id}', '{c_text}', '{s_name}', {page_no}, NULL, '{model_name}')
                        ON CONFLICT (chunk_id) DO NOTHING;
                        """
                        self.execute_query(single_sql)
                        inserted_count += 1
                    except Exception:
                        pass

        self.resequence_serial_numbers()
        return inserted_count

    def _delete_chunk_ids(self, ids: list, batch_size: int = 200) -> int:
        deleted = 0
        ids = list(ids)
        for i in range(0, len(ids), batch_size):
            batch = ids[i : i + batch_size]
            in_list = ", ".join("'" + str(c).replace("'", "''") + "'" for c in batch)
            self.execute_query(f"DELETE FROM rag_documents WHERE chunk_id IN ({in_list});")
            deleted += len(batch)
        return deleted

    def sync_chunks(self, chunks: list, embedding_model_name: str, batch_size: int = 100) -> dict:
        self.create_table_if_not_exists()
        res = self.execute_query("SELECT chunk_id, md5(chunk_text) AS h FROM rag_documents;")
        existing = {r["chunk_id"]: r["h"] for r in res.get("rows", [])}

        def clean(t):
            return str(t).replace("\x00", "")

        wanted = {c["chunk_id"]: hashlib.md5(clean(c["text"]).encode("utf-8")).hexdigest() for c in chunks}
        stale = [cid for cid in existing if cid not in wanted]
        changed = [cid for cid, h in wanted.items() if cid in existing and existing[cid] != h]
        new_ids = [cid for cid in wanted if cid not in existing]

        if stale or changed:
            self._delete_chunk_ids(stale + changed)
        inserted = self.insert_chunks(chunks, embedding_model_name=embedding_model_name, batch_size=batch_size)
        if (stale or changed) and not inserted:
            self.resequence_serial_numbers()
        return {
            "stale_deleted": len(stale),
            "changed_replaced": len(changed),
            "new_inserted": len(new_ids),
            "rows_written": inserted,
            "unchanged": len(wanted) - len(changed) - len(new_ids),
        }

    def get_stats(self):
        res_count = self.execute_query("SELECT COUNT(*) AS total FROM rag_documents;")
        total = res_count.get("rows", [{}])[0].get("total", 0)
        res_sources = self.execute_query("""
            SELECT source_name, COUNT(*) AS chunks_count, MIN(page_number) AS min_page, MAX(page_number) AS max_page
            FROM rag_documents
            GROUP BY source_name
            ORDER BY source_name;
        """)
        return {
            "total_chunks": total,
            "sources": res_sources.get("rows", []),
        }


if __name__ == "__main__":
    client = NeonDBClient()
    print("Database status:", client.test_connection())
    client.create_table_if_not_exists()
