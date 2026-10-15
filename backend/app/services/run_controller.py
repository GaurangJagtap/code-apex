import os
import uuid
import datetime
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.db.session import SessionLocal
from backend.app.db.models import (
    TestRun, ExploredPage, TestCase, TestExecution, BugFinding, Artifact, RunEvent, RegressionTest
)
from backend.app.services.browser_manager import BrowserSession
from backend.app.services.curiosity_engine import CuriosityEngine
from backend.app.services.browser_executor import BrowserExecutor
from backend.app.agents.scout import ScoutAgent
from backend.app.agents.tester import TesterAgent
from backend.app.agents.verifier_agent import VerifierAgent
from backend.app.llm.provider import LLMProvider
from backend.app.core.config import settings

class RunController:
    """
    Central Orchestrator coordinating Scout, Tester, and Verifier agents,
    driving the run state machine, recording events, and persisting execution results.
    """
    active_runs: Dict[str, bool] = {} # run_id -> is_cancelled_flag

    @classmethod
    def request_cancellation(cls, run_id: str):
        if run_id in cls.active_runs:
            cls.active_runs[run_id] = True

    @classmethod
    def is_cancelled(cls, run_id: str) -> bool:
        return cls.active_runs.get(run_id, False)

    @classmethod
    def emit_event(
        cls,
        db: Session,
        run_id: str,
        stage: str,
        agent_role: str,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        event = RunEvent(
            id=f"evt-{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            timestamp=datetime.datetime.utcnow(),
            stage=stage,
            agent_role=agent_role,
            event_type=event_type,
            message=message,
            details=details or {}
        )
        db.add(event)
        db.commit()

    @classmethod
    async def execute_run_task(cls, run_id: str):
        """
        Background task executing the complete autonomous QA lifecycle.
        """
        cls.active_runs[run_id] = False
        db = SessionLocal()
        run = db.query(TestRun).filter(TestRun.id == run_id).first()
        if not run:
            db.close()
            return

        browser_session = BrowserSession(run_id=run_id)

        try:
            # 1. INITIALIZING
            run.status = "initializing"
            run.start_time = datetime.datetime.utcnow()
            db.commit()

            cls.emit_event(
                db, run_id, "initialize", "orchestrator", "RUN_STARTED",
                f"Initializing autonomous QA session for {run.target_url}"
            )

            await browser_session.initialize(headless=settings.BROWSER_HEADLESS)

            if cls.is_cancelled(run_id):
                run.status = "cancelled"
                db.commit()
                return

            # 2. EXPLORING (Scout Agent)
            run.status = "exploring"
            db.commit()
            cls.emit_event(
                db, run_id, "explore", "scout", "SCOUT_STARTED",
                "Scout Agent inspecting DOM structure and interactive controls."
            )

            scout = ScoutAgent(base_url=run.target_url)
            page = browser_session.page
            await page.goto(run.target_url, wait_until="domcontentloaded", timeout=12000)

            inspection = await scout.inspect_page(page)
            # Store ExploredPage in DB
            db_page = ExploredPage(
                id=f"page-{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                url=inspection["url"],
                title=inspection["title"],
                status="visited",
                discovered_controls=inspection["controls"],
                navigation_links=inspection["links"],
                depth=0
            )
            db.add(db_page)
            db.commit()

            cls.emit_event(
                db, run_id, "explore", "scout", "PAGE_EXPLORED",
                f"Discovered {len(inspection['controls'])} interactive controls and {len(inspection['links'])} routes on '{inspection['title']}'",
                {"controls_count": len(inspection["controls"]), "links": inspection["links"]}
            )

            # Discover reachable catalog page if available
            catalog_link = next((l for l in inspection["links"] if "products" in l), None)
            if catalog_link:
                try:
                    await page.goto(catalog_link, wait_until="domcontentloaded", timeout=8000)
                    cat_inspection = await scout.inspect_page(page)
                    db_cat_page = ExploredPage(
                        id=f"page-{uuid.uuid4().hex[:8]}",
                        run_id=run_id,
                        url=cat_inspection["url"],
                        title=cat_inspection["title"],
                        status="visited",
                        discovered_controls=cat_inspection["controls"],
                        navigation_links=cat_inspection["links"],
                        depth=1
                    )
                    db.add(db_cat_page)
                    db.commit()
                except Exception:
                    pass

            if cls.is_cancelled(run_id):
                run.status = "cancelled"
                db.commit()
                return

            # 3. PLANNING (Tester Agent & Curiosity Engine)
            run.status = "planning"
            db.commit()
            cls.emit_event(
                db, run_id, "plan", "tester", "PLANNING_STARTED",
                "Synthesizing structured test plan using Curiosity Engine ranking."
            )

            curiosity_engine = CuriosityEngine()
            llm_provider = LLMProvider()
            tester = TesterAgent(curiosity_engine=curiosity_engine, llm_provider=llm_provider)

            planned_tests = tester.generate_test_plan(
                target_url=run.target_url,
                app_description=run.description,
                scout_observations=[inspection],
                mode=run.mode
            )

            # Persist Planned Test Cases
            db_test_cases = []
            for pt in planned_tests:
                tc = TestCase(
                    id=pt["test_id"],
                    run_id=run_id,
                    title=pt["title"],
                    category=pt["category"],
                    priority=pt["priority"],
                    priority_score=pt["priority_score"],
                    preconditions=pt.get("preconditions"),
                    steps=pt["steps"],
                    expected_results=pt.get("expected_results", []),
                    assertions=pt["assertions"],
                    status="Planned",
                    risk_reason=pt.get("risk_reason"),
                    curiosity_breakdown=pt.get("curiosity", {}),
                    regression_eligible=pt.get("regression_candidate", False)
                )
                db.add(tc)
                db_test_cases.append(tc)

            run.total_tests = len(db_test_cases)
            db.commit()

            cls.emit_event(
                db, run_id, "plan", "tester", "TEST_PLAN_APPROVED",
                f"Generated and prioritized {len(db_test_cases)} test cases with explainable curiosity scores.",
                {"test_ids": [t.id for t in db_test_cases]}
            )

            # 4. EXECUTING & VERIFYING
            run.status = "executing"
            db.commit()

            executor = BrowserExecutor(browser_session=browser_session)
            verifier = VerifierAgent(browser_executor=executor, max_retries=1)

            passed_cnt = 0
            failed_cnt = 0
            blocked_cnt = 0
            findings_cnt = 0

            for tc in db_test_cases:
                if cls.is_cancelled(run_id):
                    tc.status = "Cancelled"
                    db.commit()
                    break

                tc.status = "Running"
                db.commit()

                cls.emit_event(
                    db, run_id, "execute", "tester", "TEST_STARTED",
                    f"Executing {tc.id}: {tc.title} (Curiosity Score: {tc.priority_score})"
                )

                t_start = datetime.datetime.utcnow()
                exec_result = await executor.execute_test({
                    "steps": tc.steps,
                    "assertions": tc.assertions
                })
                t_end = datetime.datetime.utcnow()
                duration = (t_end - t_start).total_seconds()

                test_exec_id = f"exec-{uuid.uuid4().hex[:8]}"
                test_exec = TestExecution(
                    id=test_exec_id,
                    test_case_id=tc.id,
                    run_id=run_id,
                    status=exec_result["status"],
                    actual_observations="\n".join(exec_result["step_logs"]),
                    start_time=t_start,
                    end_time=t_end,
                    duration_sec=duration,
                    assertion_results=exec_result["assertion_results"],
                    screenshot_ids=exec_result["screenshot_ids"],
                    console_logs=exec_result["console_logs"]
                )
                db.add(test_exec)
                tc.status = exec_result["status"]

                # Register Screenshots as Artifacts
                for art_id in exec_result["screenshot_ids"]:
                    fname = f"{art_id}.png"
                    art_record = Artifact(
                        id=art_id,
                        run_id=run_id,
                        test_id=tc.id,
                        type="screenshot",
                        file_path=os.path.join(settings.ARTIFACTS_DIR, fname),
                        file_name=fname,
                        content_type="image/png"
                    )
                    db.add(art_record)

                if exec_result["status"] == "Passed":
                    passed_cnt += 1
                    cls.emit_event(
                        db, run_id, "execute", "tester", "TEST_PASSED",
                        f"PASSED: {tc.id} - {tc.title}"
                    )
                elif exec_result["status"] == "Blocked":
                    blocked_cnt += 1
                    cls.emit_event(
                        db, run_id, "execute", "tester", "TEST_BLOCKED",
                        f"BLOCKED: {tc.id} - {tc.title} ({exec_result.get('execution_error')})"
                    )
                else: # Failed -> Invoke Verifier Agent!
                    failed_cnt += 1
                    cls.emit_event(
                        db, run_id, "verify", "verifier", "VERIFICATION_STARTED",
                        f"Failure observed on {tc.id}. Verifier Agent starting failure replay in clean session."
                    )

                    verification = await verifier.verify_failure(
                        test_case={"steps": tc.steps, "assertions": tc.assertions, "title": tc.title},
                        initial_result=exec_result
                    )

                    # Build Proof-Carrying Bug Finding
                    bug_id = f"BUG-{uuid.uuid4().hex[:6].upper()}"
                    failed_step_texts = [s.get("description", str(s)) for s in tc.steps]
                    
                    finding = BugFinding(
                        id=bug_id,
                        run_id=run_id,
                        test_execution_id=test_exec_id,
                        title=f"Defect in {tc.title}",
                        description=f"Deterministic failure detected in {tc.category}. {verification['verification_notes']}",
                        affected_url=exec_result.get("final_url", run.target_url),
                        severity=verification["severity"],
                        severity_reason=verification["severity_reason"],
                        status=verification["finding_status"],
                        confidence_score=verification["confidence_score"],
                        verification_notes=verification["verification_notes"],
                        expected_behavior="; ".join([a.get("message") or f"Expected {a.get('type')}" for a in verification["failed_assertions"]]) or ("; ".join([a.get("message") for a in tc.assertions if a.get("message")]) or tc.title),
                        actual_behavior="; ".join([a.get("actual") or "Assertion violation" for a in verification["failed_assertions"]]) or (exec_result.get("execution_error") or "Assertion failed during browser execution"),
                        reproduction_steps=failed_step_texts,
                        screenshot_url=f"/api/v1/artifacts/{exec_result['screenshot_ids'][-1]}" if exec_result["screenshot_ids"] else None,
                        console_errors=exec_result["page_errors"],
                        replay_attempts=verification["replay_attempts"]
                    )
                    db.add(finding)
                    findings_cnt += 1

                    cls.emit_event(
                        db, run_id, "verify", "verifier", "BUG_CONFIRMED",
                        f"VERIFIED FINDING [{finding.status}]: {finding.title} (Severity: {finding.severity})",
                        {"finding_id": bug_id, "severity": finding.severity, "status": finding.status}
                    )

                db.commit()

            # 5. REPORTING
            run.status = "reporting"
            run.passed_count = passed_cnt
            run.failed_count = failed_cnt
            run.blocked_count = blocked_cnt
            run.findings_count = findings_cnt
            db.commit()

            cls.emit_event(
                db, run_id, "report", "orchestrator", "REPORTS_GENERATED",
                f"Generated proof-carrying reports: {passed_cnt} passed, {failed_cnt} failed, {findings_cnt} verified findings."
            )

            # 6. COMPLETED
            run.status = "completed" if not cls.is_cancelled(run_id) else "cancelled"
            run.end_time = datetime.datetime.utcnow()
            run.duration_sec = (run.end_time - run.start_time).total_seconds()
            db.commit()

            cls.emit_event(
                db, run_id, "completed", "orchestrator", "RUN_COMPLETED",
                f"Autonomous QA Run {run_id} finished in {run.duration_sec:.1f}s."
            )

        except Exception as e:
            run.status = "failed"
            run.error_summary = str(e)
            run.end_time = datetime.datetime.utcnow()
            db.commit()
            cls.emit_event(
                db, run_id, "failed", "orchestrator", "RUN_FAILED",
                f"Fatal run exception: {str(e)}"
            )

        finally:
            await browser_session.close()
            cls.active_runs.pop(run_id, None)
            db.close()
