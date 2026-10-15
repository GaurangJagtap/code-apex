# Controlled Sample E-Commerce Application — Seeded Defects

This document catalogues the 5 intentionally seeded defects in the DevStore Demo Application (`http://127.0.0.1:5001`). These defects are designed to test the Autonomous AI QA Engineer's capabilities: exploration, assertion execution, failure verification, and evidence generation.

---

## 1. BUG-01: Faulty Email Format Validation
- **Bug ID**: `BUG-01`
- **Location**: Registration Page (`/register`)
- **Trigger**: Submitting a registration form with an invalid email address missing `@` or domain (e.g. `invaliduser.com` or `plainaddress`) or valid emails with subaddressing `+` characters.
- **Expected Behavior**: The form should reject malformed emails with an explicit error message: `"Please provide a valid email address with @ and domain."` and block account creation.
- **Actual Defective Behavior**: The form performs a naive length-only validation (`len(email) > 3`), allowing invalid emails such as `bademail` to successfully register and create an account.
- **Verification Method**: Submit registration with `invalidemail_without_at`, assert whether the account is created or error message is shown.

---

## 2. BUG-02: Cart Subtotal Calculation Failure on Quantity Update
- **Bug ID**: `BUG-02`
- **Location**: Shopping Cart Page (`/cart`)
- **Trigger**: Updating an item's quantity in the cart from 1 to 2 (or clicking the `+` button).
- **Expected Behavior**: The item row subtotal and the cart order summary total should recompute: `Subtotal = Unit Price * Quantity`, and `Total = Subtotal + Shipping + Tax`.
- **Actual Defective Behavior**: When quantity is changed via the input or increment button, the displayed quantity value updates, but the subtotal and total calculations fail to update and remain locked at the 1-item price.
- **Verification Method**: Add item ($129.99) to cart, increment quantity to 2, read the cart total text. Expected: `$259.98` + shipping; Actual: displays `$129.99` + shipping.

---

## 3. BUG-03: Missing Validation on Required Postal/ZIP Code
- **Bug ID**: `BUG-03`
- **Location**: Checkout Page (`/checkout`)
- **Trigger**: Filling in Name, Address, City, and Country, but leaving the Postal/ZIP code field blank, then clicking "Place Order".
- **Expected Behavior**: Form validation must prevent submission and highlight the missing required Postal Code with an error: `"Postal / ZIP Code is required"`.
- **Actual Defective Behavior**: The form backend and frontend omit Postal Code validation. The order is submitted and processed successfully with a blank postal code, resulting in invalid shipping logistics.
- **Verification Method**: Attempt checkout with empty postal code; assert whether checkout is blocked with an error or confirmation page `/order-confirmation/{order_id}` is loaded.

---

## 4. BUG-04: Non-Idempotent Duplicate Order Submission
- **Bug ID**: `BUG-04`
- **Location**: Checkout Page (`/checkout`)
- **Trigger**: Rapidly submitting or re-posting the "Place Order" button.
- **Expected Behavior**: The submit button should disable during submission, and an idempotency token should prevent creating multiple identical orders.
- **Actual Defective Behavior**: The button remains active and unthrottled. Two consecutive requests generate two distinct order IDs with duplicate charges for the exact same cart.
- **Verification Method**: Send duplicate submit requests or click rapidly; query `/api/state` or check order history to find multiple orders generated within seconds.

---

## 5. BUG-05: Broken Access Control on Protected Account Route
- **Bug ID**: `BUG-05`
- **Location**: Protected Account Page (`/account`)
- **Trigger**: Directly navigating to `http://127.0.0.1:5001/account` in a clean browser session without logging in.
- **Expected Behavior**: Unauthenticated requests must redirect to `/login?redirect=/account` with a 302/303 redirect or display an unauthorized prompt.
- **Actual Defective Behavior**: The route serves the account profile and sensitive mock customer data (name, email, order history) to any anonymous visitor because session verification is completely bypassed.
- **Verification Method**: Launch browser in incognito / clean context without cookies, navigate directly to `/account`, check if page title contains "Customer Account" and profile information is visible.

---

## Reset Endpoint
- **URL**: `POST http://127.0.0.1:5001/api/reset`
- **Action**: Restores synthetic product inventory, clears carts, resets mock orders, and restores default test user (`tester@apexqa.io` / `Password123!`).
