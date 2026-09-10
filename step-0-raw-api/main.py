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
        model="claude-sonnet-5",
        # Thinking is adaptive on current models, and thinking tokens count
        # against max_tokens — so the ceiling has to cover the model's reasoning
        # as well as its answer, and a three-sentence reply can spend a few
        # hundred tokens getting there. Leave headroom. Watch `stop_reason`
        # printed below: "max_tokens" means you were cut off mid-thought and
        # should raise this number.
        max_tokens=4096,
        # `effort` is the cheapest cost lever you have: low/medium/high/xhigh
        # trades thinking depth against token spend, with no change to your
        # prompt. Worth knowing from the very first request. Note it lives
        # inside output_config, not at the top level.
        output_config={"effort": "low"},
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
