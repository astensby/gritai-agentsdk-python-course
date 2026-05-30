import asyncio

from anthropic import AsyncAnthropic

# Below the Agent SDK lives the raw Anthropic SDK: a thin HTTP client for
# the Claude REST API. There are no tools, no MCP, no skills here — just a
# single `messages.create()` call.
#
# Everything we learn in steps 1+ is built on top of this primitive. The
# Agent SDK runs a loop of these calls, threading tool results back in.


async def main() -> None:
    client = AsyncAnthropic()

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Explain what an AI agent is in three sentences."},
        ],
    )

    for block in response.content:
        if block.type == "text":
            print(block.text, end="", flush=True)

    print("\n\n---")
    print(f"Input tokens:  {response.usage.input_tokens}")
    print(f"Output tokens: {response.usage.output_tokens}")
    print(f"Stop reason:   {response.stop_reason}")


if __name__ == "__main__":
    asyncio.run(main())
