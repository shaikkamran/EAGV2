import asyncio
import yaml

from dotenv import load_dotenv
from agent.agent_loop_modified import AgentLoopModified
from mcp_servers.multiMCP import MultiMCP

BANNER = """
──────────────────────────────────────────────────────
🔸  Agentic Query Assistant  🔸
Type your question and press Enter.
Type 'exit' or 'quit' to leave.
──────────────────────────────────────────────────────
"""


async def interactive() -> None:
    load_dotenv()
    print(BANNER)
    print("Loading MCP Servers...")

    with open("config/mcp_server_config.yaml", "r") as f:
        profile = yaml.safe_load(f)
        mcp_servers_list = profile.get("mcp_servers", [])
        configs = list(mcp_servers_list)

    multi_mcp = MultiMCP(server_configs=configs)
    await multi_mcp.initialize()

    loop = AgentLoopModified(
        perception_prompt_path="prompts/perception_prompt.yaml",
        decision_prompt_path="prompts/decision_prompt.yaml",
        multi_mcp=multi_mcp,
        strategy="exploratory",
    )

    while True:
        query = input("🟢  You: ").strip()
        if query.lower() in {"exit", "quit"}:
            print("👋  Goodbye!")
            break

        response = await loop.run(query)
        print(f"🔵 Agent: {response.state['solution_summary']}\n")

        follow = input("\n\nContinue? (press Enter) or type 'exit': ").strip()
        if follow.lower() in {"exit", "quit"}:
            print("👋  Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(interactive())

