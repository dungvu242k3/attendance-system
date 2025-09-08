import numpy as np
import psycopg2
import psycopg2.extras


class FaceDatabase:
    def __init__(self, dbname="face_db", user="postgres", password="sat24042003", host="localhost", port=5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def add_face(self, employee_id, employee_code, embedding, filename=None):

        try:
            if isinstance(embedding, np.ndarray):
                emb = "[" + ",".join(map(str, embedding.astype(np.float32))) + "]"
            else:
                emb = "[" + ",".join(map(str, embedding.cpu().numpy().astype(np.float32))) + "]"

            self.cur.execute(
                """
                INSERT INTO face_embeddings (employee_id, employee_code, embedding, filename)
                VALUES (%s, %s, %s, %s)
                """,
                (employee_id, employee_code, emb, filename)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("Error in add_face:", e)

    def search_face(self, embedding, top_k=1):

        try:
            if isinstance(embedding, np.ndarray):
                emb = "[" + ",".join(map(str, embedding.astype(np.float32))) + "]"
            else:
                emb = "[" + ",".join(map(str, embedding.cpu().numpy().astype(np.float32))) + "]"

            self.cur.execute(
                """
                SELECT e.id, e.name, f.employee_code, f.filename, (f.embedding <=> %s::vector) AS distance
                FROM face_embeddings f
                JOIN employees e ON f.employee_id = e.id
                ORDER BY distance ASC
                LIMIT %s
                """,
                (emb, top_k)
            )
            return self.cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            print("Error in search_face:", e)
            return []

    def get_employee_by_code(self, code):
        try:
            self.cur.execute("SELECT * FROM employees WHERE employee_code = %s", (code,))
            return self.cur.fetchone()
        except Exception as e:
            self.conn.rollback()
            print("Error in get_employee_by_code:", e)
            return None

    def close(self):
        self.cur.close()
        self.conn.close()
