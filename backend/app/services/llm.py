from openai import OpenAI

from app.core.config import get_settings


settings = get_settings()


class LLMService:
    def __init__(self):
        self.client = (
            OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        )
        self.model = settings.openai_model

    def summarize(
        self,
        text: str,
        max_length: int = 200,
    ) -> str:
        if not self.client:
            return self._fallback_summarize(text, max_length)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize the following text concisely.",
                    },
                    {
                        "role": "user",
                        "content": text[:4000],
                    },
                ],
                max_tokens=max_length,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return self._fallback_summarize(text, max_length)

    def generate_answer(
        self,
        query: str,
        context: str,
    ) -> str:
        if not self.client:
            return self._fallback_answer(query, context)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Answer the question based on the provided context. Be concise and accurate.",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}",
                    },
                ],
                max_tokens=500,
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return self._fallback_answer(query, context)

    def _fallback_summarize(
        self,
        text: str,
        max_length: int,
    ) -> str:
        sentences = text.split(".")
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) < max_length:
                summary += sentence.strip() + ". "
            else:
                break
        return summary.strip() or text[:max_length]

    def _fallback_answer(
        self,
        query: str,
        context: str,
    ) -> str:
        return f"Based on stored memories: {context[:500]}..."


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
