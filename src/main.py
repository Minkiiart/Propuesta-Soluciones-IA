import os
import re
from typing import List
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool

# 1. Parámetros Globales
DATA_PATH = "./data/manuales"
VECTORSTORE_DIR = "./chroma_db"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# 2. Sanitizador de PII (Requerimiento CMF)
def sanitizar_entrada(texto: str) -> str:
    """Enmascara RUTs y cuentas bancarias antes de que lleguen al LLM."""
    rut_pattern = r'\b(\d{1,2}\.?\d{3}\.?\d{3}-[\dkK])\b'
    cuenta_pattern = r'\b\d{10,16}\b'
    
    texto_limpio = re.sub(rut_pattern, '[RUT_ANONIMIZADO]', texto)
    texto_limpio = re.sub(cuenta_pattern, '[CUENTA_ANONIMIZADA]', texto_limpio)
    return texto_limpio

# 3. Carga e Ingesta
def cargar_y_fragmentar_documentos():
    loader = DirectoryLoader(DATA_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documentos = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    return text_splitter.split_documents(documentos)

def inicializar_vectorstore():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    if not os.path.exists(VECTORSTORE_DIR):
        chunks = cargar_y_fragmentar_documentos()
        return Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=VECTORSTORE_DIR,
            collection_name="soporte_tef_kb"
        )
    return Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=embeddings,
        collection_name="soporte_tef_kb"
    )

# 4. Definición de Herramientas (TOOLS) para el AGENTE
vectorstore = inicializar_vectorstore()
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

@tool
def consultar_manuales_tef(query: str) -> str:
    """Útil para buscar soluciones a códigos de error ISO8583, Khipu y normativas TEF en los manuales internos."""
    docs = retriever.invoke(query)
    if not docs:
        return "No se encontró información en los manuales."
    
    resultados = []
    for doc in docs:
        fuente = doc.metadata.get("source", "Manual Desconocido")
        pagina = doc.metadata.get("page", "N/A")
        resultados.append(f"--- FUENTE: {fuente} (Pág. {pagina}) ---\n{doc.page_content}")
    
    return "\n\n".join(resultados)

@tool
def verificar_estado_servicios(servicio: str) -> str:
    """Útil para consultar el estado en tiempo real de los servidores TEF, Khipu o Switch CMF."""
    # Simulación de respuesta de API REST de Monitoreo
    estado_mock = {
        "khipu": "DEGRADADO - Latencia alta en proveedor Khipu (850ms).",
        "tef": "OPERATIVO - Servidor de Conexión Bancaria Normal.",
        "cmf": "OPERATIVO - Switch de Autorización en línea."
    }
    return estado_mock.get(servicio.lower(), "SERVICIO DESCONOCIDO: Operativo bajo parámetros normales.")

# 5. Construcción del AGENTE Inteligente
def crear_agente_soporte():
    tools = [consultar_manuales_tef, verificar_estado_servicios]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

    prompt_agente = ChatPromptTemplate.from_messages([
        ("system", """
        Eres AndesBot-TEF, Agente de Inteligencia Artificial para Soporte Nivel 2 en Banco FinTech Andes.
        
        INSTRUCCIONES DE COMPORTAMIENTO:
        1. Analiza la consulta del operador.
        2. Si la consulta menciona una caída o fallo masivo, USA PRIMERO la herramienta 'verificar_estado_servicios'.
        3. Para buscar la causa raíz y resolución de errores específicos (ISO8583, Khipu), USA la herramienta 'consultar_manuales_tef'.
        4. NUNCA inventes información. Si no encuentras la solución en las herramientas, declara: "INFORMACIÓN INSUFICIENTE: Se requiere escalar a Nivel 3".
        5. Cita siempre la fuente y página obtenida del manual al dar tu respuesta.
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    agente = create_openai_tools_agent(llm, tools, prompt_agente)
    return AgentExecutor(agent=agente, tools=tools, verbose=True)

# 6. Ejecución
if __name__ == "__main__":
    agente_executor = crear_agente_soporte()
    
    # Ejemplo de consulta recibida desde Nivel 1 con datos sensibles
    consulta_bruta = "El operador 12.345.678-9 reporta timeout ISO-8583 código 91 en la cuenta 45678912301 de Khipu. ¿Qué hacer?"
    
    # Paso A: Sanitización (Privacidad)
    consulta_sanitizada = sanitizar_entrada(consulta_bruta)
    print(f"Consulta Sanitizada: {consulta_sanitizada}\n")
    
    # Paso B: Ejecución del Agente
    respuesta = agente_executor.invoke({"input": consulta_sanitizada})
    
    print("\n================ RESPUESTA FINAL ================")
    print(respuesta["output"])