import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from services.llm_service import call_llm

load_dotenv()

async def test_text_only():
    print("\n--- Testing Text Only ---")
    messages = [{"role": "user", "content": "Скажи коротко 'Привет, мир!' и объясни, почему небо голубое. Подумай предварительно."}]
    response = await call_llm(messages)
    print("Response Content:")
    print(getattr(response, "content", "No content"))

async def test_text_and_image():
    print("\n--- Testing Text + Image ---")
    # 1x1 black pixel in base64
    b64_img = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    
    class DummyAtt:
        def __init__(self, type, url):
            self.type = type
            self.url = url
            
    attachments = [DummyAtt(type="image", url=f"data:image/png;base64,{b64_img}")]
    messages = [{"role": "user", "content": "Опиши, что ты видишь на картинке, одним коротким предложением."}]
    
    response = await call_llm(messages, attachments=attachments)
    print("Response Content:")
    print(getattr(response, "content", "No content"))

async def test_tool_calling():
    print("\n--- Testing Tool Calling ---")
    messages = [{"role": "user", "content": "Узнай текущую температуру в Москве через инструмент погоды."}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Получает текущую погоду",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "Город для поиска погоды"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    response = await call_llm(messages, tools=tools)
    print("Response Content:")
    print(getattr(response, "content", "No content"))
    if hasattr(response, "tool_calls") and response.tool_calls:
        print("Tool Calls found:")
        for tc in response.tool_calls:
            print(f"Name: {tc.function.name}, Args: {tc.function.arguments}")
    else:
        print("No tool calls found, although one was expected.")

async def main():
    await test_text_only()
    await test_text_and_image()
    await test_tool_calling()

if __name__ == "__main__":
    asyncio.run(main())
