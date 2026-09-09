import logging

import ollama

from app.core.config import Settings
from app.services.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

REFUSAL_MESSAGE_TEMPLATE = "This isn't covered in {project}'s uploaded documents."


def is_grounded_enough(hits: list[RetrievedChunk], settings: Settings) -> bool:
    if not hits:
        return False
    return hits[0].distance <= settings.distance_threshold


def build_prompt(question: str, hits: list[RetrievedChunk]) -> str:
    context_blocks = [f"[Source: {h.doc_name}, section: {h.section}]\n{h.text}" for h in hits]
    context = "\n\n".join(context_blocks)

    return f"""You are a documentation assistant. Answer the question using ONLY the context below.
If the answer is not contained in the context, say explicitly that it isn't covered in the documents -
do not guess or use outside knowledge. When you do answer, cite the source document and section for
every fact you use, in the form (doc_name, section).

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""


def generate(question: str, hits: list[RetrievedChunk], settings: Settings) -> str:
    prompt = build_prompt(question, hits)
    try:
        client = ollama.Client(host=settings.ollama_host)
        response = client.chat(model=settings.ollama_model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]
    except Exception as e:
        logger.error("Ollama call failed: %s", e)
        return (
            f"[Generation failed: could not reach Ollama at {settings.ollama_host} "
            f"with model '{settings.ollama_model}'. Is `ollama serve` running and is the model pulled?]"
        )


def refusal_message(project_label: str) -> str:
    return REFUSAL_MESSAGE_TEMPLATE.format(project=project_label)
