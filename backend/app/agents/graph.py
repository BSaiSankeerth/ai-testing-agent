from dataclasses import asdict

from langgraph.graph import END, START, StateGraph

from app.agents.analysis import analyze
from app.agents.exploration import explore
from app.agents.execution import CaseResult, order_cases, run_case
from app.agents.planning import create_plan
from app.agents.state import CaseOutcome, RunState
from app.agents.test_data import RunIdentity
from app.agents.testcase_generator import generate_test_cases
from app.agents.bug_report import create_bug_report
from app.browser.manager import BrowserManager
from app.llm.base import LLMClient, LLMError


def _say(message: str) -> None:
    print(f"[graph] {message}", flush=True)


def _fail(stage: str, message: str) -> dict:
    _say(f"{stage} FAILED: {message}")
    return {"stage": "failed", "errors": [f"{stage}: {message}"]}


def _route(next_node: str):
    """Continue to next_node unless the previous node marked the run failed."""

    def router(state: RunState) -> str:
        return END if state.get("stage") == "failed" else next_node

    return router


def build_graph(llm: LLMClient, headless: bool = True, slow_mo_ms: int = 0):
    def browser(state: RunState) -> BrowserManager:
        return BrowserManager(
            state["allowed_origins"], headless=headless, slow_mo_ms=slow_mo_ms
        )

    # --- nodes -----------------------------------------------------------
    def plan_node(state: RunState) -> dict:
        _say("planning...")
        try:
            plan = create_plan(llm, state["target_url"], state["instructions"])
        except LLMError as exc:
            return _fail("planning", str(exc)[:300])
        _say(f"plan has {len(plan.tasks)} tasks")
        return {"plan": plan, "stage": "exploring"}

    def explore_node(state: RunState) -> dict:
        _say("exploring...")
        try:
            with browser(state) as bm:
                pages = explore(bm, state["target_url"])
        except Exception as exc:
            return _fail("exploring", str(exc).splitlines()[0][:300])
        usable = [p for p in pages if "error" not in p]
        if not usable:
            return _fail("exploring", "no pages could be loaded")
        _say(f"explored {len(usable)} pages")
        return {"pages": pages, "stage": "generating"}

    def generate_node(state: RunState) -> dict:
        _say("generating test cases...")
        accepted, rejected = generate_test_cases(llm, state["plan"], state["pages"])
        if not accepted:
            return _fail("generating", "no valid test cases were produced")
        _say(f"{len(accepted)} cases accepted, {len(rejected)} rejected")
        return {"test_cases": accepted, "rejected_cases": rejected, "stage": "executing"}

    def execute_node(state: RunState) -> dict:
        identity = RunIdentity.new()  # stays inside this node
        outcomes: list[CaseOutcome] = []
        try:
            with browser(state) as bm:
                for case in order_cases(state["test_cases"]):
                    _say(f"running: {case.title}")
                    try:
                        result = run_case(bm, case, identity)
                    except Exception as exc:
                        result = CaseResult(
                            case.title,
                            "automation_error",
                            f"unexpected error: {str(exc).splitlines()[0][:200]}",
                        )
                    analysis = analyze(llm, case, result)
                    _say(f"  verdict: {analysis.verdict}")
                    outcomes.append(
                        {"case": case, "result": asdict(result), "analysis": analysis}
                    )
        except Exception as exc:
            return _fail("executing", str(exc).splitlines()[0][:300])
        return {"outcomes": outcomes, "stage": "done"}
    
    def report_node(state: RunState) -> dict:
        bugs = []
        for outcome in state.get("outcomes", []):
            draft = create_bug_report(llm, outcome)
            if draft:
                _say(f"bug report: {draft.title}")
                bugs.append({"case_title": outcome["case"].title, "bug": draft})
        _say(f"{len(bugs)} bug report(s)")
        return {"bugs": bugs}

    # --- wiring ----------------------------------------------------------
    graph = StateGraph(RunState)
    graph.add_node("plan", plan_node)
    graph.add_node("explore", explore_node)
    graph.add_node("generate", generate_node)
    graph.add_node("execute", execute_node)

    graph.add_edge(START, "plan")
    graph.add_conditional_edges("plan", _route("explore"), ["explore", END])
    graph.add_conditional_edges("explore", _route("generate"), ["generate", END])
    graph.add_conditional_edges("generate", _route("execute"), ["execute", END])
    graph.add_node("report", report_node)
    graph.add_conditional_edges("execute", _route("report"), ["report", END])
    graph.add_edge("report", END)

    return graph.compile()