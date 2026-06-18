import asyncio
import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

nest_asyncio.apply()  # Needed to run interactive python

def main():
    print("Hello from ai-wedding-planner!")


if __name__ == "__main__":
    asyncio.run(main())
