# AndesBot-TEF: Agente Inteligente de Soporte Nivel 2

> **Asignatura:** Ingeniería de Soluciones con IA (ISY0101)  
> **Institución:** Duoc UC  
> **Caso Organizacional:** Banco FinTech Andes  

---

## Descripción del Proyecto

**AndesBot-TEF** es una solución empresarial basada en **Agentes de Inteligencia Artificial (ReAct architecture)**, **LLMs (`gpt-4o-mini`)** y **RAG (Retrieval-Augmented Generation)**. Su propósito es automatizar y acelerar el diagnóstico de incidencias técnicas en Transferencias Electrónicas de Fondos (TEF) y en la pasarela de pagos Khipu (mensajería ISO 8583) para el equipo de Soporte Nivel 2 de Banco FinTech Andes.

El sistema incorpora un **Middleware de Sanitización de PII** para dar cumplimiento estricto a las regulaciones de la Comisión para el Mercado Financiero (**CMF**), garantizando la protección de datos sensibles (RUTs y cuentas bancarias) antes de cualquier interacción con modelos de lenguaje externos.

---

## Objetivos SMART del Proyecto

* **Reducción de MTTR:** Disminuir el Tiempo Medio de Resolución (MTTR) de tickets de **42 minutos a menos de 8 minutos**.
* **Disminución de Escalamientos:** Filtrar y resolver el **60% de las incidencias recurrentes** en Nivel 1 mediante un diagnóstico guiado y automatizado.
* **Cero Alucinaciones (Precisión Factual):** Anclar el 100% de las respuestas exclusivamente a manuales normativos probados y APIs de telemetría en tiempo real, activando guardrails de abstención ante falta de información.

---

## Arquitectura del Sistema

El flujo de procesamiento sigue una arquitectura desacoplada y orientada a eventos para el diagnóstico de fallas:

```text
[Operador N1 / Ticket]
          │
          ▼
┌───────────────────────────────────┐
│ 1. Middleware Sanitizador PII     │  ──► Enmascara RUTs y Cuentas Bancarias
└───────────────────────────────────┘
          │ (Consulta Anonimizada)
          ▼
┌───────────────────────────────────┐
│ 2. Agente Orquestador ReAct       │  ──► Decisión dinámica de herramientas
└───────────────────────────────────┘
          │
          ├───────────────────────────────────────────┐
          ▼                                           ▼
┌───────────────────────────────────┐       ┌───────────────────────────────────┐
│ Tool A: Estado de Servicios API   │       │ Tool B: Retriever RAG (ChromaDB) │
│ (Monitoreo TEF/Khipu/Switch CMF)  │       │ (Manuales PDF / Códigos ISO 8583) │
└───────────────────────────────────┘       └───────────────────────────────────┘
          │                                           │
          └─────────────────────┬─────────────────────┘
                                │
                                ▼
              ┌───────────────────────────────────┐
              │ 3. Generación Estructurada +      │
              │    Guardrails de Anclaje          │
              └───────────────────────────────────┘
                                │
                                ▼
                  [Diagnóstico / Solución N2]