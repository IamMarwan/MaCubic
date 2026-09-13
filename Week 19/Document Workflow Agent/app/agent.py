"""Observe -> decide -> validate -> execute -> persist -> observe again."""

import time

from app.models import InputError, PlannerError, State, TASKS
from app.policy import can_finish, eligible_tools, goal_tools
from app.tools import TOOL_SPECS


class WorkflowAgent:
    def __init__(self, settings, repository, tools, planner):
        self.settings = settings
        self.repository = repository
        self.tools = tools
        self.planner = planner

    def run(self, document, task="workflow", instruction=""):
        if not isinstance(task, str) or task not in TASKS:
            raise InputError(f"Task must be one of: {', '.join(sorted(TASKS))}.")
        if not isinstance(instruction, str) or len(instruction) > 2000:
            raise InputError("Task instruction must be a string of at most 2000 characters.")
        state = State(document, task, instruction)
        run_id = self.repository.create_run(document, task, self.planner.name)
        start = time.monotonic()
        self.repository.event(run_id, "run_started", {
            "task": task, "instruction": instruction, "provider": self.planner.name,
            "model": self.settings.model if self.planner.name == "openai" else None,
            "filename": document.filename, "pages": document.pages,
            "max_steps": self.settings.max_steps,
        })
        status, stop_reason, error = "halted", "step_limit", None
        used = []
        for step in range(1, self.settings.max_steps + 1):
            remaining = self.settings.run_timeout - (time.monotonic() - start)
            if remaining <= 0:
                stop_reason = "time_limit"
                break
            eligible = eligible_tools(state)
            finished = can_finish(state)
            self.repository.event(run_id, "planning", {
                "step": step, "available_tools": eligible, "can_finish": finished,
                "remaining_required_tools": sorted(goal_tools(state) - state.results.keys()),
            })
            try:
                decision = self.planner.next_decision(
                    state, eligible, finished, min(self.settings.request_timeout, remaining)
                )
                self.repository.event(run_id, "decision", {
                    "step": step, "tool": decision.tool, "reason": decision.reason,
                    "arguments": decision.arguments,
                })
                if time.monotonic() - start > self.settings.run_timeout:
                    stop_reason = "time_limit"
                    break
                if decision.tool == "finish":
                    if not finished:
                        raise PlannerError("Planner tried to finish before the task requirements were satisfied.")
                    status, stop_reason = "completed", "goal_satisfied"
                    break
                if decision.tool not in eligible:
                    raise PlannerError("Unavailable, repeated or prerequisite-violating tool call was blocked.")
                if not isinstance(decision.reason, str) or not 1 <= len(decision.reason.strip()) <= 500:
                    raise PlannerError("A brief decision reason is required.")
                expected = {"query"} if decision.tool == "search_knowledge_base" else set()
                if not isinstance(decision.arguments, dict) or set(decision.arguments) - expected:
                    raise PlannerError("Unexpected tool arguments were blocked.")
                query = decision.arguments.get("query", "")
                if not isinstance(query, str) or len(query) > 500:
                    raise PlannerError("Invalid search query was blocked.")
                tool_start = time.monotonic()
                self.repository.event(run_id, "tool_started", {"step": step, "tool": decision.tool})
                output = getattr(self.tools, decision.tool)(state, **decision.arguments)
                state.results[decision.tool] = output
                used.append(decision.tool)
                self.repository.event(run_id, "tool_result", {
                    "step": step, "tool": decision.tool, "output": output,
                    "duration_ms": round((time.monotonic() - tool_start) * 1000, 2),
                })
            except PlannerError as exc:
                status, stop_reason, error = "failed", "planner_error", str(exc)
                self.repository.event(run_id, "error", {"step": step, "code": stop_reason, "message": error})
                break
            except Exception as exc:
                # Do not store provider secrets, raw exceptions, or credentials.
                status, stop_reason, error = "failed", "tool_or_service_error", type(exc).__name__
                self.repository.event(run_id, "error", {"step": step, "code": stop_reason, "message": error})
                break
        skipped = {name: "Not needed or not selected for this completed task." if status == "completed"
                   else "Not executed before the run stopped." for name in TOOL_SPECS if name not in used}
        result = {
            "provider": self.planner.name, "model": self.settings.model if self.planner.name == "openai" else None,
            "tools_used": used, "tools_skipped": skipped, "outputs": state.results,
            "stop_reason": stop_reason, "error": error,
            "duration_ms": round((time.monotonic() - start) * 1000, 2),
        }
        self.repository.event(run_id, "run_finished", {"status": status, "stop_reason": stop_reason, "tools_skipped": skipped})
        self.repository.finish(run_id, status, result)
        return self.repository.get_run(run_id)
