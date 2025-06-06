from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def chat_with_llm():
    print("Chat router initialized")
    return {"response": "Hello from LLM!"}
