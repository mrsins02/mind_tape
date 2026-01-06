import pytest

from app.services.llm import LLMService


@pytest.fixture
def llm_service():
    return LLMService()


def test_fallback_summarize(llm_service):
    text = "This is a test sentence. Another sentence here. And one more."
    result = llm_service._fallback_summarize(text, max_length=50)
    assert len(result) <= 60
    assert "." in result


def test_fallback_answer(llm_service):
    query = "What is this about?"
    context = "Some context information."
    result = llm_service._fallback_answer(query, context)
    assert "Based on stored memories" in result
    assert context[:100] in result


def test_summarize_without_openai():
    service = LLMService()
    service.client = None
    text = "Test content for summarization."
    result = service.summarize(text)
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_answer_without_openai():
    service = LLMService()
    service.client = None
    result = service.generate_answer("question", "context")
    assert isinstance(result, str)
