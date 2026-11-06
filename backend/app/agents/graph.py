import uuid
from dataclasses import asdict

from langgraph.graph import END, START, StateGraph

from app.agents.analysis import analyze
from app.agents.bug_report import create_bug_report
from app.agents.exploration import explore
from app.agents.execution import CaseResult, order_cases, run_case
from app.agents.planning import create_plan
from app.agents.state import CaseOutcome, RunState
from app.agents.test_data import RunIdentity
from app.agents.testcase_generator import generate_test_cases
from app.browser.manager import BrowserManager
from app.llm.base import LLMClient, LLMError
from app.services.progress import report_progress


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
        report_progress(state.get("session_id"), stage="planning", current_case=None)
        try:
            plan = create_plan(llm, state["target_url"], state["instructions"])
        except LLMError as exc:
            return _fail("planning", str(exc)[:300])
        _say(f"plan has {len(plan.tasks)} tasks")
        report_progress(state.get("session_id"), case_total=len(plan.tasks))
        return {"plan": plan, "stage": "exploring"}

    def explore_node(state: RunState) -> dict:
        _say("exploring...")
        report_progress(state.get("session_id"), stage="exploring")
        try:
            with browser(state) as bm:
                pages = explore(bm, state["target_url"])
        except Exception as exc:
            return _fail("exploring", str(exc).splitlines()[0][:300])
        usable = [p for p in pages if "error" not in p]
        if not usable:
            return _fail("exploring", "no pages could be loaded")
        _say(f"explored {len(usable)} pages")
        report_progress(state.get("session_id"), pages_explored=len(usable))
        return {"pages": pages, "stage": "generating"}

    def generate_node(state: RunState) -> dict:
        _say("generating test cases...")
        report_progress(state.get("session_id"), stage="generating")
        accepted, rejected = generate_test_cases(llm, state["plan"], state["pages"])
        if not accepted:
            failure = _fail("generating", "no valid test cases were produced")
            failure["rejected_cases"] = rejected  # keep the reasons for the database
            return failure
        _say(f"{len(accepted)} cases accepted, {len(rejected)} rejected")
        report_progress(state.get("session_id"), case_total=len(accepted))
        return {"test_cases": accepted, "rejected_cases": rejected, "stage": "executing"}

    def execute_node(state: RunState) -> dict:
        sid = state.get("session_id")
        identity = RunIdentity.new()  # stays inside this node
        outcomes: list[CaseOutcome] = []
        shots_dir = f"storage/screenshots/{uuid.uuid4().hex[:12]}"
        ordered = order_cases(state["test_cases"])
        report_progress(sid, stage="executing", case_total=len(ordered), case_index=0)
        try:
            with browser(state) as bm:
                for index, case in enumerate(ordered, start=1):
                    _say(f"running: {case.title}")
                    report_progress(sid, current_case=case.title, case_index=index)
                    try:
                        result = run_case(bm, case, identity, shots_dir=shots_dir)
                    except Exception as exc:
                        result = CaseResult(
                            case.title,
                            "automation_error",
                            f"unexpected error: {str(exc).splitlines()[0][:200]}",
                        )
                    analysis = analyze(llm, case, result)
                    _say(f"  verdict: {analysis.verdict}")
                    report_progress(
                        sid,
                        finished=[
                            *(_finished(sid)),
                            {"title": case.title, "verdict": analysis.verdict},
                        ],
                    )
                    outcomes.append(
                        {"case": case, "result": asdict(result), "analysis": analysis}
                    )
        except Exception as exc:
            return _fail("executing", str(exc).splitlines()[0][:300])
        return {"outcomes": outcomes, "stage": "done"}

    def report_node(state: RunState) -> dict:
        report_progress(state.get("session_id"), stage="reporting", current_case=None)
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
    graph.add_node("report", report_node)

    graph.add_edge(START, "plan")
    graph.add_conditional_edges("plan", _route("explore"), ["explore", END])
    graph.add_conditional_edges("explore", _route("generate"), ["generate", END])
    graph.add_conditional_edges("generate", _route("execute"), ["execute", END])
    graph.add_conditional_edges("execute", _route("report"), ["report", END])
    graph.add_edge("report", END)

    return graph.compile()

#
def _finished(session_id: int | None) -> list:
    """Verdicts reported so far for this session (so each new one is appended)."""
    if session_id is None:
        return []
    from app.db.models import TestSession
    from app.db.session import SessionLocal

    try:
        with SessionLocal() as db:
            s = db.get(TestSession, session_id)
            return list((s.progress or {}).get("finished", [])) if s else []
    except Exception:
        return []