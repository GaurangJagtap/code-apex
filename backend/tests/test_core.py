import pytest
from backend.app.core.security import is_url_allowed, sanitize_logs
from backend.app.services.curiosity_engine import CuriosityEngine
from backend.app.schemas.qa_schemas import TestCaseCreate, TestStepSchema, AssertionSchema

def test_url_security_boundaries():
    # Valid allowed URLs
    assert is_url_allowed("http://127.0.0.1:5001") == True
    assert is_url_allowed("http://localhost:5001/products") == True

    # Blocked dangerous schemes
    assert is_url_allowed("file:///etc/passwd") == False
    assert is_url_allowed("ftp://example.com") == False
    assert is_url_allowed("javascript:alert(1)") == False

    # Blocked AWS/Cloud metadata address
    assert is_url_allowed("http://169.254.169.254/latest/meta-data/") == False

    # Blocked external untrusted domains
    assert is_url_allowed("https://malicious-external-site.com") == False

def test_sensitive_credential_redaction():
    raw = 'User login payload: password="SecretPassword123!" and token="eyJh...token"'
    sanitized = sanitize_logs(raw)
    assert "SecretPassword123!" not in sanitized
    assert "[REDACTED]" in sanitized

def test_curiosity_engine_scoring():
    engine = CuriosityEngine()

    # Transactional high-impact journey should score significantly higher than standard static navigation
    score_cart = engine.evaluate_candidate(
        candidate_id="TEST-CART",
        title="Cart Subtotal Recomputation",
        category="Business-rule testing",
        path="http://127.0.0.1:5001/cart",
        description="Core checkout transaction",
        business_criticality=0.9
    )

    score_faq = engine.evaluate_candidate(
        candidate_id="TEST-FAQ",
        title="Static FAQ Page Link",
        category="Navigation",
        path="http://127.0.0.1:5001/faq",
        description="Static information",
        business_criticality=0.1
    )

    assert score_cart["priority_score"] > score_faq["priority_score"]
    assert "cart" in score_cart["reasoning"].lower() or "transactional" in score_cart["reasoning"].lower()

def test_test_case_schema_validation():
    tc = TestCaseCreate(
        test_id="TC-01",
        title="Check Button Exists",
        category="Functional",
        priority="High",
        steps=[
            TestStepSchema(action="goto", value="http://127.0.0.1:5001", description="Open page"),
            TestStepSchema(action="click", selector="#btn-submit", description="Click submit")
        ],
        assertions=[
            AssertionSchema(type="element_visible", target="#success-message", message="Should show success")
        ],
        risk_reason="Sanity check"
    )
    assert tc.test_id == "TC-01"
    assert len(tc.steps) == 2
    assert tc.assertions[0].type == "element_visible"
