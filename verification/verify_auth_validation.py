from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Navigate to Auth page
    page.goto("http://localhost:3000")

    # Wait for the form to appear
    expect(page.get_by_text("Welcome back")).to_be_visible()

    # Try to submit empty form
    page.get_by_role("button", name="Log In").click()

    # Check for validation errors
    # Expect "Email is required" and "Password is required"
    expect(page.get_by_text("Email is required")).to_be_visible()
    expect(page.get_by_text("Password is required")).to_be_visible()

    page.screenshot(path="verification/auth_empty_validation.png")

    # Fill invalid email
    page.get_by_label("Email Address").fill("invalid-email")
    page.get_by_role("button", name="Log In").click()
    expect(page.get_by_text("Please enter a valid email address")).to_be_visible()

    page.screenshot(path="verification/auth_invalid_email.png")

    # Fill valid email but short password
    page.get_by_label("Email Address").fill("test@example.com")
    page.get_by_label("Password", exact=True).fill("123")
    page.get_by_role("button", name="Log In").click()
    expect(page.get_by_text("Password must be at least 6 characters")).to_be_visible()

    page.screenshot(path="verification/auth_short_password.png")

    # Switch to Signup
    page.get_by_text("Don't have an account? Sign Up").click()

    # Verify errors are cleared
    expect(page.get_by_text("Password must be at least 6 characters")).not_to_be_visible()

    # Try empty signup
    page.get_by_role("button", name="Create Account").click()
    expect(page.get_by_text("Name is required")).to_be_visible()

    page.screenshot(path="verification/auth_signup_validation.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
