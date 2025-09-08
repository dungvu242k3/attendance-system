import numpy as np


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return 1 - np.dot(a, b)


class FaceRecognizer:
    def __init__(self, database, threshold=0.7):
        self.database = database
        self.threshold = threshold

    def recognize(self, embedding):
        if embedding is None:
            return None, "Unknown", None, None

        if not isinstance(embedding, np.ndarray):
            if hasattr(embedding, "cpu"):
                embedding = embedding.cpu().numpy()
            else:
                embedding = np.array(embedding)

        results = self.database.search_face(embedding, top_k=1)
        if not results:
            return None, "Unknown", None, None

        employee_id, name, employee_code, filename, distance = results[0]

        if distance <= self.threshold:
            confidence = 1 - distance
            return employee_id, name, distance, confidence
        else:
            return None, "Unknown", distance, 1 - distance
