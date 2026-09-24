import os
import chromadb
from sentence_transformers import SentenceTransformer

MANUAL_PATH = os.path.join("data", "manuales", "Manual_Errores_ISO8583_TEF.txt")
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "iso8583_manual"

def parse_manual_into_chunks(file_path: str):
    """
    Lee el manual y lo divide en chunks estructurados basándose en las secciones
    de códigos de error ISO 8583 / DE39.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No se encontró el manual en: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Dividir por bloques de error (asumiendo formato del manual)
    raw_blocks = content.split("----------------------------------------")
    chunks = []
    
    for i, block in enumerate(raw_blocks):
        clean_block = block.strip()
        if clean_block:
            chunks.append({
                "id": f"chunk_{i+1}",
                "text": clean_block
            })
            
    return chunks

def build_vector_store():
    print("1. Cargando manual técnico...")
    chunks = parse_manual_into_chunks(MANUAL_PATH)
    print(f"   Encontrados {len(chunks)} bloques de información.")

    print("2. Cargando modelo de Embeddings (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    print("3. Inicializando ChromaDB local...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Eliminar colección previa si existe para asegurar ingesta limpia
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Manual de Errores ISO 8583 Banco FinTech Andes"}
    )

    print("4. Generando embeddings y guardando en ChromaDB...")
    documents = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    embeddings = model.encode(documents).tolist()

    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids
    )

    print(f"✅ Ingesta exitosa. Base vectorial guardada en './{CHROMA_PATH}'")

if __name__ == "__main__":
    build_vector_store()
    