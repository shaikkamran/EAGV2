from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

from action.executor import run_user_code
from agent.agentSession import AgentSession, PerceptionSnapshot, Step, ToolCode
from agent.context_builders import build_decision_context, build_perception_context
from decision.decision_modified import Decision
from mcp_servers.multiMCP import MultiMCP
from perception.perception_modified import Perception


@dataclass
class LoopBlock:
    name: str
    context: Optional[dict] = None
    output: Optional[dict] = None

    def update(self, *, context: dict, output: dict) -> dict:
        self.context = context
        self.output = output
        return output


class AgentLoopModified:
    def __init__(
        self,
        perception_prompt_path: str = "prompts/perception_prompt.yaml",
        decision_prompt_path: str = "prompts/decision_prompt.yaml",
        multi_mcp: Optional[MultiMCP] = None,
        strategy: str = "exploratory",
    ):
        if multi_mcp is None:
            raise ValueError("A MultiMCP instance is required for the agent loop.")

        self.perception = Perception(perception_prompt_path)
        self.decision = Decision(decision_prompt_path)
        self.multi_mcp = multi_mcp
        self.strategy = strategy
        self.blocks: Dict[str, LoopBlock] = {
            "perception": LoopBlock("perception"),
            "decision": LoopBlock("decision"),
        }
        self._cached_tool_descriptions: Optional[List[str]] = None

    async def run(self, query: str) -> AgentSession:
        session = AgentSession(session_id=str(uuid.uuid4()), original_query=query)

        perception_ctx = build_perception_context(original_user_query=query)
        initial_perception = self._record_block(
            "perception",
            perception_ctx,
            self.perception.get_perception_output(perception_ctx),
        )
        perception_snapshot = PerceptionSnapshot(**self._normalize_perception_output(initial_perception))
        session.add_perception(perception_snapshot)

        if perception_snapshot.original_goal_achieved:
            session.mark_complete(perception_snapshot, perception_snapshot.solution_summary)
            return session

        decision_ctx = build_decision_context(
            plan_mode="initial",
            planning_strategy=self.strategy,
            original_user_query=query,
            perception_object=initial_perception,
            current_plan_text=[],
            completed_steps=[],
            recent_step_feedback="Initial planning request.",
            available_tools=self._get_available_tools(),
        )

        decision_output = self._record_block(
            "decision",
            decision_ctx,
            self.decision.get_decision_output(decision_ctx),
        )
        current_step = self._store_plan_and_return_step(session, decision_output)
        completed_steps: List[Step] = []

        while current_step:
            if current_step.type == "CODE":
                await self._execute_code_step(query, session, current_step)
            elif current_step.type == "CONCLUDE":
                self._process_conclusion_step(query, session, current_step)
                break
            else:  # NOP / clarification request
                session.state.update(
                    {
                        "original_goal_achieved": False,
                        "final_answer": current_step.conclusion,
                        "confidence": 0.0,
                        "reasoning_note": "Decision agent requested clarification.",
                    }
                )
                break

            completed_steps.append(current_step)
            if session.state["original_goal_achieved"]:
                break

            perception_payload = current_step.perception.__dict__ if current_step.perception else {}
            decision_ctx = build_decision_context(
                plan_mode="mid_session",
                planning_strategy=self.strategy,
                original_user_query=query,
                perception_object=perception_payload,
                current_plan_text=session.plan_versions[-1]["plan_text"],
                completed_steps=completed_steps,
                recent_step_feedback=self._build_recent_feedback(current_step),
                available_tools=self._get_available_tools(),
            )
            decision_output = self._record_block(
                "decision",
                decision_ctx,
                self.decision.get_decision_output(decision_ctx),
            )
            current_step = self._store_plan_and_return_step(session, decision_output)

        return session

    def _record_block(self, name: str, context: dict, output: dict) -> dict:
        block = self.blocks.setdefault(name, LoopBlock(name))
        return block.update(context=context, output=output)

    def _normalize_perception_output(self, payload: Optional[dict]) -> dict:
        defaults = {
            "entities": [],
            "result_requirement": "N/A",
            "original_goal_achieved": False,
            "reasoning": "",
            "local_goal_achieved": False,
            "local_reasoning": "",
            "last_tooluse_summary": "",
            "solution_summary": "Not ready yet",
            "confidence": "0.0",
        }
        if payload:
            defaults.update({k: payload.get(k, defaults[k]) for k in defaults})
        return defaults

    def _store_plan_and_return_step(self, session: AgentSession, decision_output: dict) -> Optional[Step]:
        if not decision_output:
            return None

        plan_text = decision_output.get("plan_text") or []
        next_step = decision_output.get("next_step") or {}

        if not next_step:
            return None

        expected_index = session.get_next_step_index()
        proposed_index = next_step.get("step_index")
        if not isinstance(proposed_index, int) or proposed_index < expected_index:
            step_index = expected_index
        else:
            step_index = proposed_index

        step_type = next_step.get("type", "NOP")
        step_code = next_step.get("code", "")
        step = Step(
            index=step_index,
            description=next_step.get("description", "No description provided."),
            type=step_type,
            code=ToolCode(tool_name="raw_code_block", tool_arguments={"code": step_code}) if step_type == "CODE" else None,
            conclusion=next_step.get("conclusion"),
        )

        session.add_plan_version(plan_text if isinstance(plan_text, list) else [plan_text], [step])
        return step

    async def _execute_code_step(self, query: str, session: AgentSession, step: Step) -> None:
        if not step.code:
            step.status = "failed"
            step.error = "Missing code payload."
            return

        executor_response = await run_user_code(step.code.tool_arguments.get("code", ""), self.multi_mcp)

        print(f"\n\n\n\n\nExecutor Response: {executor_response}\n\n\n\n\n")
        step.execution_result = executor_response.get("result")
        step.error = executor_response.get("error")
        step.status = "completed" if executor_response.get("status") == "success" else "failed"

        perception_ctx = build_perception_context(
            original_user_query=query,
            plan_from_decision_agent=session.plan_versions[-1]["plan_text"],
            current_step_index=step.index,
            result_of_current_step=step.execution_result or step.error or "Tool execution returned no output.",
        )
        perception_output = self._record_block(
            "perception",
            perception_ctx,
            self.perception.get_perception_output(perception_ctx),
        )
        perception_snapshot = PerceptionSnapshot(**self._normalize_perception_output(perception_output))
        step.perception = perception_snapshot

        if perception_snapshot.original_goal_achieved:
            session.mark_complete(perception_snapshot, step.execution_result)

    def _process_conclusion_step(self, query: str, session: AgentSession, step: Step) -> None:
        perception_ctx = build_perception_context(
            original_user_query=query,
            plan_from_decision_agent=session.plan_versions[-1]["plan_text"] if session.plan_versions else [],
            current_step_index=step.index,
            result_of_current_step=step.conclusion or "Conclusion provided with no summary.",
        )
        perception_output = self._record_block(
            "perception",
            perception_ctx,
            self.perception.get_perception_output(perception_ctx),
        )
        perception_snapshot = PerceptionSnapshot(**self._normalize_perception_output(perception_output))
        step.perception = perception_snapshot
        session.mark_complete(perception_snapshot, step.conclusion)

    def _build_recent_feedback(self, step: Step) -> str:
        result_text = step.execution_result or ""
        error_text = step.error or ""
        perception_summary = step.perception.solution_summary if step.perception else ""
        return "\n".join(
            filter(
                None,
                [
                    f"Step {step.index}: {step.description}",
                    f"Status: {step.status}",
                    f"Result: {result_text}" if result_text else None,
                    f"Error: {error_text}" if error_text else None,
                    f"Perception: {perception_summary}" if perception_summary else None,
                ],
            )
        )

    def _get_available_tools(self) -> List[str]:
        if self._cached_tool_descriptions is None:
            self._cached_tool_descriptions = self.multi_mcp.tool_description_wrapper()
        return self._cached_tool_descriptions

