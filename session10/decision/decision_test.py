from decision import Decision
from mcp_servers.multiMCP import MultiMCP

import json
import yaml

with open("config/mcp_server_config.yaml", "r") as f:
    profile = yaml.safe_load(f)
    mcp_servers_list = profile.get("mcp_servers", [])
    configs = list(mcp_servers_list)


def test_decision():
    decision = Decision(decision_prompt_path="prompts/decision_prompt.txt", multi_mcp=MultiMCP(server_configs=configs))
    result = decision.run(
        decision_input={
            "plan_mode": "initial",
            "planning_strategy": "conservative",
            "original_query": "Find number of BHK variants available in DLF Camelia from local sources.",
            "perception": {
                "entities": ["DLF Camelia", "BHK variants", "local sources"],
                "result_requirement": "Numerical count of distinct BHK configurations...",
                "original_goal_achieved": False,
                "reasoning": "The user wants...",
                "local_goal_achieved": False,
                "local_reasoning": "This is just perception, no data retrieved yet."
            }
        }
    )
    print(json.dumps(result, indent=2))
    print(result)

test_decision()
