import hashlib
from typing import Dict, Any, List
from backend.app.services.browser_executor import BrowserExecutor

class VerifierAgent:
    """
    Verifier Agent: Evaluates failures independently, isolates minimal reproduction
    sequences, verifies reproducibility across controlled browser sessions, and classifies
    finding statuses with evidence-backed rules.
    """
    def __init__(self, browser_executor: BrowserExecutor, max_retries: int = 1):
        self.executor = browser_executor
        self.max_retries = max_retries

    def construct_minimal_reproduction_sequence(
        self,
        test_case: Dict[str, Any],
        initial_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extracts the minimal contiguous sequence of actions needed to reach and trigger
        the defect, stripping redundant trailing steps or auxiliary screenshots.
        """
        all_steps = test_case.get("steps", [])
        if not all_steps:
            return []

        # Find the point where execution failed or assertions broke
        step_logs = initial_result.get("step_logs", [])
        failed_step_idx = None
        for i, log in enumerate(step_logs):
            if "FAILED" in log:
                failed_step_idx = i
                break

        if failed_step_idx is not None:
            # Include steps up to the failure point
            minimal = all_steps[: failed_step_idx + 1]
        else:
            # All steps ran, but assertions failed: keep functional actions, omit redundant trailing screenshots
            minimal = [s for s in all_steps if s.get("action") not in ("screenshot",)]
            if not minimal:
                minimal = list(all_steps)

        return minimal

    def generate_dedup_key(self, affected_url: str, title: str, failed_assertions: List[Dict[str, Any]]) -> str:
        """Computes a stable deduplication fingerprint for the root defect."""
        from urllib.parse import urlparse
        path = urlparse(affected_url).path or "/"
        target = failed_assertions[0].get("target", "") if failed_assertions else ""
        a_type = failed_assertions[0].get("type", "") if failed_assertions else ""
        raw = f"{path}:{target}:{a_type}:{title[:30]}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]

    async def verify_failure(
        self,
        test_case: Dict[str, Any],
        initial_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Replays the failing test with a minimal reproduction sequence in an isolated context.
        """
        minimal_steps = self.construct_minimal_reproduction_sequence(test_case, initial_result)
        repro_test = {
            "steps": minimal_steps,
            "assertions": test_case.get("assertions", []),
            "title": f"Minimal Repro: {test_case.get('title', '')}"
        }

        replay_attempts = 1
        reproduced_count = 1
        replay_results = [initial_result]

        for i in range(self.max_retries):
            replay_attempts += 1
            res = await self.executor.execute_test(repro_test)
            replay_results.append(res)
            if res["status"] == "Failed":
                reproduced_count += 1

        # Evaluate Status Classification
        initial_status = initial_result.get("status")
        execution_error = initial_result.get("execution_error")
        assertion_results = initial_result.get("assertion_results", [])
        failed_assertions = [a for a in assertion_results if not a.get("passed")]

        # Classify using explicit evidence-based rules
        if initial_status == "Blocked" or (execution_error and "timeout" in execution_error.lower()):
            finding_status = "Inconclusive"
            reason = "Test execution was blocked by an environmental timeout or missing locator rather than an application logic defect."
            confidence = 0.60

        elif reproduced_count == replay_attempts and failed_assertions:
            finding_status = "Verified"
            reason = f"Deterministic defect reproduced with consistent supporting evidence across {replay_attempts} independent browser sessions."
            confidence = 0.98

        elif reproduced_count > 1:
            finding_status = "Likely"
            reason = f"Strong evidence observed: defect reproduced in {reproduced_count} of {replay_attempts} controlled replay cycles."
            confidence = 0.80

        else:
            finding_status = "Not reproduced"
            reason = f"The failure observed in the initial test attempt did not recur during controlled replay validation (0/{self.max_retries} reproductions)."
            confidence = 0.40

        # Severity Assessment Policy
        title_lower = test_case.get("title", "").lower()
        if "access control" in title_lower or "security" in title_lower:
            severity = "Critical"
            severity_reason = "Unauthorized data disclosure / broken access control policy violation (CWE-284)."
        elif "cart" in title_lower or "checkout" in title_lower or "order" in title_lower or "idempotency" in title_lower:
            severity = "High"
            severity_reason = "Directly impacts core business transactions, order placement, or revenue calculation."
        elif "email" in title_lower or "validation" in title_lower or "postal" in title_lower:
            severity = "Medium"
            severity_reason = "User account or delivery data integrity defect with functional workaround."
        else:
            severity = "Low"
            severity_reason = "Minor UI or layout discrepancy without breaking transactional integrity."

        affected_url = initial_result.get("final_url", "")
        dedup_key = self.generate_dedup_key(affected_url, test_case.get("title", ""), failed_assertions)

        return {
            "finding_status": finding_status,
            "confidence_score": confidence,
            "verification_notes": reason,
            "severity": severity,
            "severity_reason": severity_reason,
            "replay_attempts": replay_attempts,
            "reproduced_count": reproduced_count,
            "failed_assertions": failed_assertions,
            "minimal_steps": minimal_steps,
            "dedup_key": dedup_key
        }
