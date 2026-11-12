import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from app.rag import Chunk, SearchResult

load_dotenv()

class SynthesisEngine:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_base = os.getenv("OPENAI_BASE_URL")
        self.preferred_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash"
        ]

    def generate_answer(
        self, 
        query: str, 
        search_results: List[SearchResult], 
        found: bool,
        requested_provider: str = "auto"
    ) -> Dict[str, Any]:
        """
        Pure Universal RAG synthesis: Given ANY user question and retrieved chunks,
        constructs a grounded context prompt and generates the response using the LLM.
        Zero hardcoded query matching.
        """
        # If guardrail flagged out-of-scope or no chunks retrieved
        if not found or not search_results:
            return {
                "answer": (
                    "**Not found in documents.**\n\n"
                    "The provided plant SOPs and manuals do not contain information regarding this request. "
                    "Please check with your Shift Supervisor, Maintenance Manager, or refer to the machine's "
                    "OEM operations manual and CAM programming sheets."
                ),
                "found": False,
                "confidence": 0.0,
                "provider": "Universal Guardrail",
                "citations": [],
                "revision_alert": None
            }

        # Build revision freshness metadata (only show warning if document is superseded)
        top_chunk = search_results[0].chunk
        revision_alert = None
        if not top_chunk.is_active:
            revision_alert = {
                "type": "warning",
                "message": (
                    f"⚠️ **Attention**: This document ({top_chunk.doc_id} {top_chunk.revision}) is **SUPERSEDED** "
                    f"by {top_chunk.superseded_by or 'a newer revision'}. Please consult the active revision for latest plant standards."
                )
            }

        # Collect citations
        citations = []
        seen_chunks = set()
        for res in search_results:
            c = res.chunk
            if c.chunk_id not in seen_chunks:
                seen_chunks.add(c.chunk_id)
                citations.append({
                    "doc_id": c.doc_id,
                    "filename": c.filename,
                    "revision": c.revision,
                    "is_active": c.is_active,
                    "effective_date": c.effective_date,
                    "section_number": c.section_number,
                    "section_title": c.section_title,
                    "page_number": c.page_number,
                    "excerpt": c.content[:350].strip() + ("..." if len(c.content) > 350 else ""),
                    "score": round(res.score, 2)
                })

        # Universal LLM generation
        try:
            if self.gemini_key:
                answer = self._call_gemini(query, search_results)
                return {
                    "answer": answer,
                    "found": True,
                    "confidence": 0.98,
                    "provider": "Google Gemini (gemini-3.1-flash-lite)",
                    "citations": citations,
                    "revision_alert": revision_alert
                }
            elif self.openai_key:
                answer = self._call_openai(query, search_results)
                return {
                    "answer": answer,
                    "found": True,
                    "confidence": 0.98,
                    "provider": f"OpenAI ({os.getenv('OPENAI_MODEL', 'gpt-4o-mini')})",
                    "citations": citations,
                    "revision_alert": revision_alert
                }
            else:
                return {
                    "answer": "Error: No LLM API key configured. Please set GEMINI_API_KEY in .env.",
                    "found": False,
                    "confidence": 0.0,
                    "provider": "Missing API Key",
                    "citations": citations,
                    "revision_alert": revision_alert
                }
        except Exception as e:
            return {
                "answer": f"LLM Generation Error: {str(e)}",
                "found": False,
                "confidence": 0.0,
                "provider": "LLM Error",
                "citations": citations,
                "revision_alert": revision_alert
            }

    def _call_gemini(self, query: str, results: List[SearchResult]) -> str:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=self.gemini_key)

        context_blocks = []
        for i, r in enumerate(results):
            c = r.chunk
            context_blocks.append(
                f"--- [EXCERPT {i+1}] Document: {c.doc_id} | Revision: {c.revision} | {c.section_number}: {c.section_title} | Page: {c.page_number} ---\n"
                f"{c.content}"
            )
        context_str = "\n\n".join(context_blocks)

        prompt = f"""You are the BiztelAI Shop Floor Copilot for Kaveri Precision Components (Hosur Plant).
Your job is to provide direct, accurate, and complete operational guidance for shop floor supervisors and technicians based STRICTLY on the document excerpts provided below.

INSTRUCTIONS:
1. Answer the question directly using ONLY facts from the provided excerpts.
2. Clearly state all key values, numbers, units, tolerances, torque specs, alarm actions, and safety rules in **bold**.
3. At the end of your answer, provide the exact Document ID, Revision, Section, and Page Number as a citation.
4. If the provided excerpts do NOT contain the information needed to answer the question, state:
   "Not found in documents. The provided plant SOPs and manuals do not contain information regarding this request."
   Do NOT guess, assume, or fabricate.
5. If an excerpt indicates it is superseded (e.g. Rev 03 superseded by Rev 04), ensure your answer reflects the active revision.

CONTEXT EXCERPTS:
{context_str}

SUPERVISOR QUESTION:
{query}

ANSWER:"""

        config = types.GenerateContentConfig(
            max_output_tokens=1000,
            temperature=0.0
        )

        last_error = None
        for model_name in self.preferred_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

    def _call_openai(self, query: str, results: List[SearchResult]) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_key, base_url=self.openai_base)

        context_blocks = []
        for i, r in enumerate(results):
            c = r.chunk
            context_blocks.append(
                f"[Source {i+1}]: {c.doc_id} {c.revision} (Page {c.page_number}, {c.section_number}: {c.section_title})\n{c.content}"
            )
        context_str = "\n\n---\n\n".join(context_blocks)

        system_prompt = (
            "You are BiztelAI Shop Floor Copilot for Kaveri Precision Components (Hosur Plant).\n"
            "Answer the supervisor's question accurately and concisely using ONLY the provided document excerpts.\n"
            "Highlight key numbers, tolerances, parameters, alarms, and procedures in bold.\n"
            "Cite the exact document number, revision, section, and page number in your answer.\n"
            "If the answer is NOT present in the excerpts, state: 'Not found in documents.'"
        )

        user_content = f"CONTEXT EXCERPTS:\n{context_str}\n\nQUESTION: {query}"
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
