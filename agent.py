import os
import chromadb
from sentence_transformers import SentenceTransformer
from sanitizer import CMFDataSanitizer

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "iso8583_manual"

SYSTEM_PROMPT = """
Eres el Agente Diagnóstico de Operaciones TEF / ISO 8583 del Banco FinTech Andes.
Tu función es diagnosticar fallas en transacciones electrónicas de fondos cumpliendo estrictamente con las normas CMF.

Reglas de Negocio:
1. Analiza el log sanitizado introducido por el usuario.
2. Basándote ÚNICAMENTE en el contexto recuperado de la Base de Conocimientos (RAG), identifica el código de respuesta (DE39 / MTI).
3. Responde siempre en el siguiente formato estricto:

---
### 🚨 DIAGNÓSTICO OPERATIVO - BANCO FINTECH ANDES
* **Código de Respuesta (DE39):** [Código e Indicador]
* **Significado Técnico:** [Explicación técnica del error]
* **Causa Raíz Probable:** [Causa según el manual]
* **Acción Correctiva Recomendada:** [Pasos a seguir por el operador/sistema]
* **Cumplimiento Normativo CMF:** [Aviso sobre protección de datos/RUT]
---
"""

class ISO8583DiagnosticAgent:
    def __init__(self):
        self.sanitizer = CMFDataSanitizer()
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)

    def retrieve_context(self, query: str, top_k: int = 2) -> str:
        """Realiza la búsqueda semántica en la base de datos vectorial."""
        query_vector = self.embedding_model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_vector,
            n_results=top_k
        )
        
        retrieved_docs = results['documents'][0]
        return "\n\n".join(retrieved_docs)

    def diagnose(self, raw_log: str) -> dict:
        # Paso 1: Sanitización CMF
        sanitized_log = self.sanitizer.sanitize_log(raw_log)
        
        # Paso 2: Recuperación RAG (Retriever)
        context = self.retrieve_context(sanitized_log)
        
        # Paso 3: Ensamblado del Prompt Final
        final_prompt = f"{SYSTEM_PROMPT}\n\n[CONTEXTO RECUPERADO DEL MANUAL]:\n{context}\n\n[LOG A DIAGNOSTICAR]:\n{sanitized_log}"
        
        return {
            "sanitized_log": sanitized_log,
            "retrieved_context": context,
            "constructed_prompt": final_prompt
        }

if __name__ == "__main__":
    agent = ISO8583DiagnosticAgent()
    sample_log = "2026-09-24 10:15:30 [ERROR] MTI 0210 - DE39=51 - Transaccion fallida para cliente RUT 19.876.543-2 con tarjeta 4509123456789012. Fondos insuficientes."
    
    print("\n================ TESTING AGENTE ISO 8583 ================")
    res = agent.diagnose(sample_log)
    print("\n1. LOG SANITIZADO (CMF):")
    print(res["sanitized_log"])
    print("\n2. CONTEXTO RECUPERADO (RAG):")
    print(res["retrieved_context"])
    