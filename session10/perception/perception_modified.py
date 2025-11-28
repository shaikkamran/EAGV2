from utils import (
    generate_llm_response,
    get_final_prompt,
    parse_response,
    read_yaml_template,
    log_prompt,
)
from enum import Enum


# Write an enum for perception context keys
class PerceptionContextKeys(Enum):
    CURRENT_STATE = "current_state"
    ORIGINAL_USER_QUERY = "original_user_query"
    PLAN_FROM_DECISION_AGENT = "plan_from_decision_agent"
    CURRENT_STEP_INDEX = "current_step_index"
    RESULT_OF_CURRENT_STEP = "result_of_current_step"


class Perception:
    def __init__(self, prompt_template_path: str):
        self.prompt_template_path = prompt_template_path
        self.prompt_template = read_yaml_template(prompt_template_path)

    def get_perception_output(self, context: dict) -> dict:

        for key in PerceptionContextKeys:
            if key.value not in context:
                raise ValueError(f"Context must contain {key.value}")

        final_prompt = get_final_prompt(self.prompt_template, context)

        log_prompt("Perception", final_prompt)
        response = generate_llm_response(
            final_prompt["system_prompt"], final_prompt["formatted_user_prompt"]
        )

        json_response = parse_response(response)
        print(f"Perception Output: {json_response}")
        return json_response


if __name__ == "__main__":

    # Inputs

    #     Current State:
    #   {{current_state}}

    #   Original User Query:
    #   {{original_user_query}}

    #   Plan from the Decision Agent:
    #   {{plan_from_decision_agent}}

    #   Current Step Index:
    #   {{current_step_index}}

    #   Result of the Current Step from the Execution:
    #   {{result_of_current_step}}

    current_state = "Initial"
    original_user_query = "What is the capital of France?"
    plan_from_decision_agent = "No plan yet - initial query state"
    current_step_index = "N/A - Initial state"
    result_of_current_step = "No result yet - initial query state"

    example_context = {
        "current_state": current_state,
        "original_user_query": original_user_query,
        "plan_from_decision_agent": plan_from_decision_agent,
        "current_step_index": current_step_index,
        "result_of_current_step": result_of_current_step,
    }

    import json

    def read_json_file(file_path: str) -> dict:
        with open(file_path, "r") as file:
            return json.load(file)

    def write_json_file(data: dict, file_path: str) -> None:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    perception_test_examples = read_json_file("perception_test_examples.json")

    import time

    output_data = []
    for example in perception_test_examples["examples"]:
        example_context = example["inputs"]
        print(example_context)

        time.sleep(2)
        final_prompt = get_final_prompt(context=example_context)
        response = generate_llm_response(
            final_prompt["system_prompt"], final_prompt["formatted_user_prompt"]
        )
        output_data.append(
            {
                "example": example["name"],
                "context": example_context,
                "final_prompt": final_prompt,
                "response": parse_response(response),
            }
        )
    write_json_file(output_data, "perception_test_examples_output.json")

    # output = get_final_prompt(context=example_context)

    # response = generate_llm_response(output['system_prompt'], output['formatted_user_prompt'])

    # print(response)
