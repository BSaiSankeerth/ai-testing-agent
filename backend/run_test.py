from app.llm.groq_client import GroqClient
from app.browser.manager import BrowserManager
from app.agents.planning import create_plan
from app.agents.exploration import explore
from app.agents.testcase_generator import generate_test_cases
from app.agents.test_data import RunIdentity
from app.agents.execution import order_cases, run_case

llm = GroqClient()
url = "http://localhost:3000"
plan = create_plan(llm, url,
    "Test the registration and login functionality. Verify valid registration, "
    "duplicate email registration, invalid email, empty fields, successful login, "
    "and incorrect password.")
print("PLAN TASKS:", len(plan.tasks))

allowed = ["http://localhost:3000", "http://localhost:8000"]
identity = RunIdentity.new()
with BrowserManager(allowed, headless=False) as bm:
    pages = explore(bm, url)
    cases, rejected = generate_test_cases(llm, plan, pages)
    print(f"{len(cases)} cases, {len(rejected)} rejected")
    for r in rejected:
        print("  REJECTED:", r)
    for case in order_cases(cases):
        r = run_case(bm, case, identity)
        print(f"\n[{r.status.upper()}] {r.title}  ({r.duration_ms} ms)")
        print("   detail:", r.detail)
        print("   url:", r.final_url)
        print("   unmet:", r.unmet_expectations)
        print("   api:", [(c['method'], c['status'], c['url'].split('8000')[-1]) for c in r.api_calls])
        print("   page:", r.page_text[:150].replace("\n", " | "))
    print("\nregistered:", identity.registered)
