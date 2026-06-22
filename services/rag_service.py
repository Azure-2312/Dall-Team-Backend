import os
import json
import hashlib
import numpy as np
from google import genai as _genai_new
from google.genai import types as _gtypes_new
from openai import OpenAI
from services.gemini_client_manager import gemini_manager

class RAGService:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        
        # Configure OpenAI if available
        self.openai_client = OpenAI(api_key=self.openai_key) if self.openai_key else None

    def get_embedding(self, text: str) -> list:
        """
        Generates a 1536-dimensional embedding.
        Uses OpenAI text-embedding-3-small/ada-002, Gemini embedding-001, or fallback deterministic mock.
        """
        if not text:
            return [0.0] * 1536
            
        # 1. Try OpenAI
        if self.openai_key and self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    input=[text],
                    model="text-embedding-3-small" # 1536 dims
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"OpenAI Embedding Error: {e}. Falling back...")
                
        # 2. Try Gemini (Note: Gemini embeddings are usually 768, we pad/repeat to 1536 if needed)
        if gemini_manager.keys:
            try:
                def embed_op(client, model_name):
                    return client.models.embed_content(
                        model="models/gemini-embedding-2",
                        contents=text
                    )
                result = gemini_manager.execute_with_retry(embed_op)
                emb = result.embeddings[0].values
                # Pad/repeat to match 1536
                if len(emb) < 1536:
                    emb = list(emb) + list(emb)[:1536 - len(emb)]
                return list(emb[:1536])
            except Exception as e:
                print(f"Gemini Embedding Error: {e}. Falling back...")

        # 3. Fallback: Deterministic Mock Embedding
        return self._generate_mock_embedding(text)

    def _generate_mock_embedding(self, text: str) -> list:
        """
        Generates a deterministic 1536-dim unit vector based on word hashes.
        Provides realistic cosine similarity between text chunks sharing similar words.
        """
        vector = np.zeros(1536)
        words = text.lower().split()
        if not words:
            words = ["default"]
            
        for word in words:
            # Hash the word to seed numpy's random state
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            np.random.seed(h % (2**32))
            vector += np.random.uniform(-1, 1, 1536)
            
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()

    def cosine_similarity(self, vec_a: list, vec_b: list) -> float:
        """Helper to calculate similarity manually for SQLite fallback."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def generate_quiz_questions(self, topic: str, context: str, count: int = 3) -> list:
        """
        Generates multiple-choice quiz questions based on the week's theme and textbook material.
        Forces structured JSON outputs from LLMs.
        """
        system_prompt = (
            "Eres un evaluador académico estricto de la UNFV. Genera preguntas de opción múltiple basadas "
            "en el tema y los apuntes/lecturas provistas. Devuelve ÚNICAMENTE un objeto JSON válido con la "
            "siguiente estructura:\n"
            "{\n"
            "  \"questions\": [\n"
            "    {\n"
            "      \"question\": \"¿Texto de la pregunta?\",\n"
            "      \"options\": [\"Opción A\", \"Opción B\", \"Opción C\", \"Opción D\"],\n"
            "      \"correct_index\": 0,\n"
            "      \"feedback\": \"Explicación detallada de por qué la respuesta es correcta.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        user_prompt = f"Tema: {topic}\nContexto: {context}\nCantidad de preguntas: {count}"

        # 1. Try Gemini
        if gemini_manager.keys:
            try:
                def quiz_op(client, model_name):
                    return client.models.generate_content(
                        model=model_name,
                        contents=[system_prompt, user_prompt],
                        config=_gtypes_new.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                response = gemini_manager.execute_with_retry(quiz_op)
                data = json.loads(response.text)
                return data.get("questions", [])
            except Exception as e:
                print(f"Gemini Quiz Generation Error: {e}. Falling back...")

        # 2. Try OpenAI
        if self.openai_key and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                data = json.loads(response.choices[0].message.content)
                return data.get("questions", [])
            except Exception as e:
                print(f"OpenAI Quiz Generation Error: {e}. Falling back...")

        # 3. Local Seeder / Rule-based QA Fallback
        return self._get_mock_quiz_questions(topic, count)

    def analyze_sentiment_and_stress(self, text: str) -> dict:
        """
        Analyzes a student query to assess stress, anxiety, or frustration.
        Returns a JSON payload with stress level and empathetic guidance suggestions.
        """
        system_prompt = (
            "Analiza el texto de un estudiante que muestra frustración o estrés académico. "
            "Devuelve un JSON estrictamente estructurado así:\n"
            "{\n"
            "  \"nivel_estres\": \"alto|medio|bajo\",\n"
            "  \"detecto_frustracion\": true|false,\n"
            "  \"consejo_empatico\": \"Mensaje corto y motivador enfocado en su bienestar y derivación a la OBU si aplica\"\n"
            "}"
        )
        
        # 1. Try Gemini
        if gemini_manager.keys:
            try:
                def sentiment_op(client, model_name):
                    return client.models.generate_content(
                        model=model_name,
                        contents=[system_prompt, f"Texto del estudiante: {text}"],
                        config=_gtypes_new.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                response = gemini_manager.execute_with_retry(sentiment_op)
                return json.loads(response.text)
            except Exception as e:
                print(f"Gemini Sentiment Analysis Error: {e}. Falling back...")

        # 2. Try OpenAI
        if self.openai_key and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Texto del estudiante: {text}"}
                    ],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"OpenAI Sentiment Analysis Error: {e}. Falling back...")

        # 3. Rule-based Sentiment Fallback
        lower_text = text.lower()
        high_stress_words = ["cansado", "rendir", "estresado", "colapsar", "jalar", "retiro", "renunciar", "dormir", "ansiedad", "pánico", "imposible", "no puedo", "loco"]
        
        matches = [w for w in high_stress_words if w in lower_text]
        if len(matches) >= 2:
            return {
                "nivel_estres": "alto",
                "detecto_frustracion": True,
                "consejo_empatico": "Detectamos una alta carga de estrés en tus palabras. Respira hondo. Recuerda que no estás solo, puedes hacer una pausa y la Oficina de Bienestar Universitario (OBU) está lista para apoyarte."
            }
        elif len(matches) == 1:
            return {
                "nivel_estres": "medio",
                "detecto_frustracion": True,
                "consejo_empatico": "El ciclo UNFV puede ser demandante. Intenta tomar un descanso corto e hidratarte antes de seguir estudiando."
            }
        else:
            return {
                "nivel_estres": "bajo",
                "detecto_frustracion": False,
                "consejo_empatico": "¡Sigue adelante con tu preparación académica! Estás yendo por buen camino."
            }

    def _get_mock_quiz_questions(self, topic: str, count: int) -> list:
        """Preseeded educational database of questions based on typical UNFV FIIS courses."""
        db_questions = [
            {
                "topic_keywords": ["algoritmo", "programacion", "estructura"],
                "questions": [
                    {
                        "question": "¿Cuál es la complejidad temporal en el peor caso para buscar un elemento en un árbol binario de búsqueda balanceado (AVL)?",
                        "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                        "correct_index": 1,
                        "feedback": "En un árbol binario de búsqueda balanceado (como un AVL), la altura máxima está limitada a O(log n), garantizando búsquedas en este orden."
                    },
                    {
                        "question": "¿Qué estructura de datos opera bajo el principio LIFO (Last In, First Out)?",
                        "options": ["Cola (Queue)", "Lista enlazada", "Pila (Stack)", "Grafo"],
                        "correct_index": 2,
                        "feedback": "Una pila (Stack) procesa los elementos bajo la modalidad LIFO (último en entrar, primero en salir)."
                    }
                ]
            },
            {
                "topic_keywords": ["base de datos", "sql", "relacional"],
                "questions": [
                    {
                        "question": "¿Qué nivel de normalización requiere eliminar dependencias transitivas en una tabla relacional?",
                        "options": ["Primera Forma Normal (1FN)", "Segunda Forma Normal (2FN)", "Tercera Forma Normal (3FN)", "Forma Normal de Boyce-Codd (BCFN)"],
                        "correct_index": 2,
                        "feedback": "La Tercera Forma Normal (3FN) requiere que la tabla esté en 2FN y que no existan dependencias transitivas de atributos no clave sobre la clave primaria."
                    },
                    {
                        "question": "¿Cuál es el propósito principal de una clave foránea (Foreign Key) en PostgreSQL?",
                        "options": ["Mejorar la velocidad de búsqueda", "Asegurar la integridad referencial", "Garantizar la unicidad de registros", "Encriptar datos sensibles"],
                        "correct_index": 1,
                        "feedback": "La clave foránea vincula registros entre tablas garantizando que el valor referenciado exista obligatoriamente en la tabla de origen."
                    }
                ]
            },
            {
                "topic_keywords": ["operaciones", "programacion lineal", "simplex"],
                "questions": [
                    {
                        "question": "En Programación Lineal, ¿qué indica una variable de holgura en el análisis del Simplex?",
                        "options": ["La holgura de tiempo del proyecto", "La cantidad de recurso no utilizado en una restricción menor o igual", "El costo de oportunidad de producir una unidad extra", "El rango permitido de variación del coeficiente de la función objetivo"],
                        "correct_index": 1,
                        "feedback": "Una variable de holgura representa la diferencia matemática entre el recurso disponible y el consumido en una restricción del tipo <=."
                    }
                ]
            }
        ]

        matched_questions = []
        topic_lower = topic.lower()
        for category in db_questions:
            if any(kw in topic_lower for kw in category["topic_keywords"]):
                matched_questions.extend(category["questions"])
        
        # Generic fallback questions if no keywords match
        if not matched_questions:
            matched_questions = [
                {
                    "question": f"Con respecto al tema '{topic}', ¿cuál es el principio metodológico principal para estructurar un estudio de caso en la UNFV?",
                    "options": [
                        "Revisión bibliográfica teórica exhaustiva previa a la experimentación",
                        "Desarrollo empírico sin delimitación conceptual",
                        "Aplicación directa de fórmulas sin análisis contextual",
                        "Retiro temporal del sílabo oficial"
                    ],
                    "correct_index": 0,
                    "feedback": "La metodología académica UNFV exige consolidar las lecturas del sílabo antes del desarrollo empírico."
                },
                {
                    "question": f"En el contexto de '{topic}', ¿cuál es el factor clave para optimizar recursos en el ciclo 2026-I?",
                    "options": [
                        "Asistencia regular al pabellón físico de tutorías obligatorias",
                        "Ignorar las fechas de la Resolución 6119-2025",
                        "Evitar el uso de Koha bibliográfico",
                        "Estudiar los temas de la semana 16 durante la semana 1"
                    ],
                    "correct_index": 0,
                    "feedback": "La tutoría presencial regular y el seguimiento semanal del sílabo son las claves del éxito estudiantil."
                }
            ]
            
        # Shuffle/limit output
        import random
        random.shuffle(matched_questions)
        return matched_questions[:count]
