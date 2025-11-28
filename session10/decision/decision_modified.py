from utils import generate_llm_response,get_final_prompt,parse_response,read_yaml_template,log_prompt
from enum import Enum
from pprint import pprint

class DecisionContextKeys(Enum):
    PLAN_MODE = "plan_mode"
    PLANNING_STRATEGY = "planning_strategy"
    ORIGINAL_USER_QUERY = "original_user_query"
    PERCEPTION_OBJECT = "perception_object"
    CURRENT_PLAN_TEXT = "current_plan_text"
    COMPLETED_STEPS = "completed_steps"
    RECENT_STEP_FEEDBACK = "recent_step_feedback"
    AVAILABLE_TOOLS = "available_tools"


class Decision:
    def __init__(self,prompt_template_path: str):
        self.prompt_template_path = prompt_template_path
        self.prompt_template = read_yaml_template(prompt_template_path)

    def get_decision_output(self,context: dict) -> dict:
        for key in DecisionContextKeys:
            if key.value not in context:
                raise ValueError(f"Context must contain {key.value}")
        final_prompt = get_final_prompt(self.prompt_template,context)

        log_prompt("Decision", final_prompt)
        response = generate_llm_response(final_prompt['system_prompt'], final_prompt['formatted_user_prompt'])
        json_response = parse_response(response)
        print(f"\n\n\n\n\nDecision Output\n\n\n\n\n")
        pprint(json_response)
        return json_response

if __name__ == "__main__":

    import json
    def write_json_file(data: dict, file_path: str) -> None:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)


    example_context = {
        "plan_mode": "initial",
        "planning_strategy": "exploratory",
        "original_user_query": "Find number of BHK variants available in DLF Camelia from local sources.",
        "perception_object": {
            "entities": ["DLF Camelia", "BHK variants", "local sources"],
            "result_requirement": "Numerical count of distinct BHK configurations in DLF Camelia, based on local data.",
            "original_goal_achieved": False,
            "confidence": "0.2",
            "reasoning": "We still need local retrieval to answer the original question.",
            "local_goal_achieved": False,
            "local_reasoning": "No retrieval executed yet.",
            "last_tooluse_summary": "init: no tool yet",
            "solution_summary": "Not ready yet"
        },
        "current_plan_text": [],
        "completed_steps": [],
        "recent_step_feedback": "",
        "available_tools": [
            "search_local_documents_rag",
            "search_web",
        ]
    }
    
    
    decision = Decision(prompt_template_path="prompts/decision_prompt.yaml")
    decision_output = decision.get_decision_output(example_context)
    print(decision_output)

    write_json_file(decision_output, "decision_output.json")