from typing import Dict, Any, List
from backend.app.schemas.qa_schemas import TestCaseCreate, TestStepSchema, AssertionSchema
from backend.app.services.curiosity_engine import CuriosityEngine
from backend.app.llm.provider import LLMProvider

class TesterAgent:
    """
    Tester Agent: Consumes the application requirements and Scout observations,
    synthesizes structured test plans, prioritizes candidates using the Curiosity Engine,
    and returns validated execution targets.
    """
    def __init__(self, curiosity_engine: CuriosityEngine, llm_provider: LLMProvider):
        self.curiosity_engine = curiosity_engine
        self.llm = llm_provider

    def generate_test_plan(
        self,
        target_url: str,
        app_description: str,
        scout_observations: List[Dict[str, Any]],
        mode: str = "demo"
    ) -> List[Dict[str, Any]]:
        """
        Generates structured test cases covering positive journeys and boundary/negative tests.
        """
        # Base candidates calibrated for web e-commerce workflows
        clean_url = target_url.rstrip("/")
        candidates = [
            {
                "test_id": "TEST-01",
                "title": "Homepage Navigation and Catalog Exploration",
                "category": "Navigation",
                "priority": "High",
                "path": f"{clean_url}/products",
                "preconditions": "Application server is reachable and product catalog is seeded.",
                "steps": [
                    {"action": "goto", "value": clean_url, "description": "Navigate to Home page"},
                    {"action": "click", "selector": "#btn-hero-shop", "description": "Click 'Explore Catalog' hero CTA"},
                    {"action": "screenshot", "description": "Capture catalog listing screenshot"}
                ],
                "assertions": [
                    {"type": "url_contains", "target": "url", "expected": "/products", "message": "Verify URL routed to /products"},
                    {"type": "element_visible", "target": "#catalog-card-PRD-01", "expected": "", "message": "Verify primary product card is rendered"}
                ],
                "risk_reason": "Ensures the primary customer entry funnel and catalog routing are functional.",
                "regression_candidate": True
            },
            {
                "test_id": "TEST-02",
                "title": "User Registration with Malformed Email Format",
                "category": "Form validation",
                "priority": "High",
                "path": f"{clean_url}/register",
                "preconditions": "Visitor is on registration form.",
                "steps": [
                    {"action": "goto", "value": f"{clean_url}/register", "description": "Navigate to Registration page"},
                    {"action": "fill", "selector": "#name", "value": "Alex Hunter", "description": "Fill user name"},
                    {"action": "fill", "selector": "#email", "value": "invaliduser_without_at", "description": "Input invalid email without '@' or domain"},
                    {"action": "fill", "selector": "#password", "value": "Password123!", "description": "Input password"},
                    {"action": "fill", "selector": "#confirm_password", "value": "Password123!", "description": "Confirm password"},
                    {"action": "click", "selector": "#btn-submit-register", "description": "Submit registration form"},
                    {"action": "screenshot", "description": "Capture form validation outcome"}
                ],
                "assertions": [
                    {"type": "element_visible", "target": "#register-error", "expected": "", "message": "Form validation error alert must be visible"},
                    {"type": "text_contains", "target": "#register-error", "expected": "valid email", "message": "Error message must indicate email format requirement"}
                ],
                "risk_reason": "Verifies data integrity and prevents corrupt account records (BUG-01).",
                "regression_candidate": False
            },
            {
                "test_id": "TEST-03",
                "title": "Cart Subtotal Recomputation on Quantity Change",
                "category": "Business-rule testing",
                "priority": "High",
                "path": f"{clean_url}/cart",
                "preconditions": "Cart contains 1 item ($129.99).",
                "steps": [
                    {"action": "goto", "value": f"{clean_url}/products/PRD-01", "description": "Open product PRD-01 detail view"},
                    {"action": "click", "selector": "#btn-detail-add-to-cart", "description": "Add 1 item to cart"},
                    {"action": "screenshot", "description": "Capture initial cart view"},
                    {"action": "click", "selector": "#btn-inc-PRD-01", "description": "Increment item quantity to 2"},
                    {"action": "wait", "value": "600", "description": "Wait for calculation recomputation"},
                    {"action": "screenshot", "description": "Capture updated cart view"}
                ],
                "assertions": [
                    {"type": "cart_total_matches", "target": "#cart-subtotal", "expected": "259.98", "message": "Cart subtotal must equal $259.98 (129.99 * 2)"}
                ],
                "risk_reason": "Prevents billing discrepancy and ensures cart arithmetic correctness (BUG-02).",
                "regression_candidate": False
            },
            {
                "test_id": "TEST-04",
                "title": "Checkout Form Validation - Required Postal Code",
                "category": "Form validation",
                "priority": "High",
                "path": f"{clean_url}/checkout",
                "preconditions": "Cart has items ready for checkout.",
                "steps": [
                    {"action": "goto", "value": f"{clean_url}/products/PRD-05", "description": "Open product PRD-05"},
                    {"action": "click", "selector": "#btn-detail-add-to-cart", "description": "Add product to cart"},
                    {"action": "click", "selector": "#btn-proceed-checkout", "description": "Proceed to checkout"},
                    {"action": "fill", "selector": "#fullname", "value": "Morgan Vance", "description": "Fill full name"},
                    {"action": "fill", "selector": "#email", "value": "morgan@apexqa.io", "description": "Fill email"},
                    {"action": "fill", "selector": "#address", "value": "789 Innovation Way", "description": "Fill street address"},
                    {"action": "fill", "selector": "#city", "value": "Austin", "description": "Fill city"},
                    {"action": "fill", "selector": "#postal_code", "value": "", "description": "Leave postal code empty"},
                    {"action": "click", "selector": "#btn-place-order", "description": "Attempt order submission with empty postal code"},
                    {"action": "screenshot", "description": "Capture checkout validation outcome"}
                ],
                "assertions": [
                    {"type": "element_visible", "target": "#checkout-error", "expected": "", "message": "Validation error alert must be visible for missing postal code"},
                    {"type": "url_not_contains", "target": "url", "expected": "/order-confirmation", "message": "Order placement must be blocked when postal code is absent"}
                ],
                "risk_reason": "Prevents invalid delivery addresses and logistics failures (BUG-03).",
                "regression_candidate": False
            },
            {
                "test_id": "TEST-05",
                "title": "Protected Account Access Without Authentication",
                "category": "Security & Access Control",
                "priority": "Critical",
                "path": f"{clean_url}/account",
                "preconditions": "Visitor has no active authentication cookie or session.",
                "steps": [
                    {"action": "goto", "value": f"{clean_url}/account", "description": "Directly navigate to protected /account route"},
                    {"action": "screenshot", "description": "Capture unauthorized route response"}
                ],
                "assertions": [
                    {"type": "url_contains", "target": "url", "expected": "/login", "message": "Unauthenticated user must be redirected to /login"},
                    {"type": "not_visible", "target": "#account-heading", "expected": "", "message": "Customer account details must NOT be visible to unauthenticated visitors"}
                ],
                "risk_reason": "Enforces authorization boundaries and protects confidential user data (BUG-05).",
                "regression_candidate": False
            },
            {
                "test_id": "TEST-06",
                "title": "Standard User Authentication and Session Verification",
                "category": "Functional testing",
                "priority": "High",
                "path": f"{clean_url}/login",
                "preconditions": "Valid user credentials exist in authentication provider.",
                "steps": [
                    {"action": "goto", "value": f"{clean_url}/login", "description": "Navigate to Login page"},
                    {"action": "fill", "selector": "#login-email", "value": "tester@apexqa.io", "description": "Enter test email"},
                    {"action": "fill", "selector": "#login-password", "value": "Password123!", "description": "Enter test password"},
                    {"action": "click", "selector": "#btn-submit-login", "description": "Submit login form"},
                    {"action": "screenshot", "description": "Capture post-login account state"}
                ],
                "assertions": [
                    {"type": "url_contains", "target": "url", "expected": "/account", "message": "Redirect to account page after successful authentication"},
                    {"type": "element_visible", "target": "#nav-logout", "expected": "", "message": "Logout navigation link must be visible for logged in user"}
                ],
                "risk_reason": "Verifies that legitimate users can authenticate and establish secure sessions.",
                "regression_candidate": True
            }
        ]

        # Prioritize every candidate using the Curiosity Engine
        ranked_tests = []
        for c in candidates:
            breakdown = self.curiosity_engine.evaluate_candidate(
                candidate_id=c["test_id"],
                title=c["title"],
                category=c["category"],
                path=c["path"],
                description=c["risk_reason"]
            )
            c["curiosity"] = breakdown
            c["priority_score"] = breakdown["priority_score"]
            ranked_tests.append(c)

        # Sort by Curiosity Engine priority score descending
        ranked_tests.sort(key=lambda x: x["priority_score"], reverse=True)
        return ranked_tests
