from typing import Dict, Any, List, Optional
from playwright.async_api import Page

class AssertionEngine:
    """
    Deterministic Assertion Engine for reliable, evidence-backed evaluation
    of application behavior against explicit user expectations.
    """
    @staticmethod
    async def evaluate_assertion(page: Page, assertion: Dict[str, Any]) -> Dict[str, Any]:
        a_type = assertion.get("type", "text_contains")
        target = assertion.get("target", "")
        expected = assertion.get("expected", "")
        message = assertion.get("message") or f"Assert {a_type} on '{target}'"

        passed = False
        actual = ""
        error_detail = None

        try:
            if a_type == "element_visible":
                loc = page.locator(target).first
                passed = await loc.is_visible(timeout=3000)
                actual = f"Element '{target}' visible: {passed}"

            elif a_type == "not_visible":
                loc = page.locator(target).first
                count = await loc.count()
                if count == 0:
                    passed = True
                    actual = f"Element '{target}' count is 0 (absent)"
                else:
                    visible = await loc.is_visible(timeout=1000)
                    passed = not visible
                    actual = f"Element '{target}' visible: {visible}"

            elif a_type == "text_contains":
                if target and target.startswith(("#", ".", "[", "body", "h1", "h2", "h3", "p", "div", "span")):
                    loc = page.locator(target).first
                    if await loc.count() > 0:
                        text_val = await loc.inner_text(timeout=3000)
                    else:
                        text_val = await page.content()
                else:
                    text_val = await page.content()
                
                passed = expected.lower() in text_val.lower()
                actual = f"Found text segment in page: {passed}"

            elif a_type == "url_contains":
                curr_url = page.url
                passed = expected.lower() in curr_url.lower()
                actual = f"Current URL is '{curr_url}', expected to contain '{expected}'"

            elif a_type == "url_not_contains":
                curr_url = page.url
                passed = expected.lower() not in curr_url.lower()
                actual = f"Current URL is '{curr_url}', expected NOT to contain '{expected}'"

            elif a_type == "value_matches":
                loc = page.locator(target).first
                actual_val = await loc.input_value(timeout=2000)
                passed = (str(actual_val).strip() == str(expected).strip())
                actual = f"Input value was '{actual_val}', expected '{expected}'"

            elif a_type == "cart_total_matches":
                # Verifies arithmetic equality: subtotal = price * quantity
                # e.g., target is unit price selector, expected is quantity * price
                loc_subtotal = page.locator("#cart-subtotal").first
                subtotal_text = await loc_subtotal.inner_text()
                # Parse numeric value from "$129.99"
                import re
                nums = re.findall(r"[\d\.]+", subtotal_text)
                if nums:
                    val = float(nums[0])
                    expected_float = float(expected)
                    # Allow 0.05 margin for currency
                    passed = abs(val - expected_float) < 0.05
                    actual = f"Subtotal displayed ${val:.2f}, expected ${expected_float:.2f}"
                else:
                    passed = False
                    actual = f"Unable to parse subtotal from '{subtotal_text}'"

            elif a_type == "element_disabled":
                loc = page.locator(target).first
                if await loc.count() > 0:
                    is_disabled = await loc.is_disabled()
                    has_attr = await loc.evaluate("el => el.hasAttribute('disabled') || el.classList.contains('disabled')")
                    passed = bool(is_disabled or has_attr)
                    actual = f"Element '{target}' disabled status: {passed}"
                else:
                    passed = False
                    actual = f"Element '{target}' not found"

            elif a_type == "element_enabled":
                loc = page.locator(target).first
                if await loc.count() > 0:
                    passed = await loc.is_enabled()
                    actual = f"Element '{target}' enabled: {passed}"
                else:
                    passed = False
                    actual = f"Element '{target}' not found"

            else:
                passed = False
                actual = f"Unknown assertion type '{a_type}'"

        except Exception as e:
            passed = False
            actual = f"Assertion exception: {str(e)}"
            error_detail = str(e)

        return {
            "type": a_type,
            "target": target,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "message": message,
            "error_detail": error_detail
        }
