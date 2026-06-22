import asyncio
from app.services.llm_provider import llm_service

async def test():
    p = llm_service.get_active()
    print(f'Provider: {p.descriptor.display_name} ({p.descriptor.name})')
    result = await p.call(
        system_prompt='You are a test. Output JSON only.',
        user_prompt='Reply with {"status":"ok","model":"working"}',
        temperature=0.1,
        max_tokens=50,
    )
    print(f'Result: {result}')
    stats = p.get_usage_stats()
    print(f'Calls: {stats["total_calls"]}, Tokens: {stats["total_prompt_tokens"]}+{stats["total_completion_tokens"]}')

asyncio.run(test())
