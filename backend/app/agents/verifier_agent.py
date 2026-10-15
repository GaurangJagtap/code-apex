from typing import Dict, Any, List
from backend.app.services.browser_executor import BrowserExecutor

class VerifierAgent:
    """
    Verifier Agent: Replays suspicious test failures in an isolated browser context,
    checks consistency across attempts, and classifies the finding status.
    """
    def __init__(self, browser_executor: BrowserExecutor, max_retries: int = 1):
        self.executor = browser_executor
        self.max_retries = max_retries

    async def verify_failure(
        self,
        test_case: Dict[str, Any],
        initial_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Replays the failing test in a fresh browser session to evaluate reproducibility.
        """
        replay_attempts = 1
        reproduced_count = 1
        replay_results = [initial_result]

        for i in range(self.max_retries):
            replay_attempts += 1
            res = await self.executor.execute_test(test_case)
            replay_results.append(res)
            if res["status"] == "Failed":
                reproduced_count += 1

        # Evaluate Status Classification
        initial_status = initial_result.get("status")
        execution_error = initial_result.get("execution_error")
        assertion_results = initial_result.get("assertion_results", [])
        failed_assertions = [a for a in assertion_results if not a.get("passed")]

        if initial_status == "Blocked" or (execution_error and "timeout" in execution_error.lower()):
            finding_status = "Inconclusive"
            reason = "Test execution was blocked by an environmental timeout or locator inability rather than an application logic defect."
            confidence = 0.60

        elif reproduced_count == replay_attempts and failed_assertions:
            finding_status = "Confirmed"
            reason = f"Deterministic assertion failure reproduced consistently across {replay_attempts} independent browser sessions."
            confidence = 0.98

        elif reproduced_count > 1:
            finding_status = "Suspected"
            reason = f"Intermittent failure: defect occurred in {reproduced_count} out of {replay_attempts} replay sessions."
            confidence = 0.75

        else:
            finding_status = "Not Reproducible"
            reason = f"The failure observed in the initial test attempt did not reproduce upon replay (0/{self.max_retries} reproductions)."
            confidence = 0.40

        # Severity Assessment Policy
        title_lower = test_case.get("title", "").lower()
        if "access control" in title_lower or "security" in title_lower:
            severity = "Critical"
            severity_reason = "Unauthorized data disclosure / broken access control policy violation."
        elif "cart" in title_lower or "checkout" in title_lower or "order" in title_lower or "total" in title_lower:
            severity = "High"
            severity_reason = "Directly impacts core business transactions and revenue processing."
        elif "email" in title_lower or "validation" in title_lower:
            severity = "Medium"
            severity_reason = "User account data integrity defect with viable workaround."
        else:
            severity = "Low"
            severity_reason = "Minor UI discrepancy without breaking transactions."

        return {
            "finding_status": finding_status,
            "confidence_score": confidence,
            "verification_notes": reason,
            "severity": severity,
            "severity_reason": severity_reason,
            "replay_attempts": replay_attempts,
            "reproduced_count": reproduced_count,
            "failed_assertions": failed_assertions
        }
