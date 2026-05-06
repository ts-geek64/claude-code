import { test, expect } from "@playwright/test";

const LOGIN_URL = "/login";

test.describe("Login page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(LOGIN_URL);
  });

  // ─── Rendering ────────────────────────────────────────────────────────────

  test("renders the login form", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Welcome back" }),
    ).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  // ─── Validation errors ────────────────────────────────────────────────────

  test("shows validation errors when submitting empty form", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(
      page.getByText("Please enter a valid email address"),
    ).toBeVisible();
    await expect(
      page.getByText("Password must be at least 8 characters"),
    ).toBeVisible();
  });

  test("shows email validation error for invalid email", async ({ page }) => {
    await page.getByLabel("Email").fill("not-an-email");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(
      page.getByText("Please enter a valid email address"),
    ).toBeVisible();
  });

  test("shows password validation error for short password", async ({
    page,
  }) => {
    await page.getByLabel("Email").fill("user@example.com");
    await page.getByLabel("Password").fill("short");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(
      page.getByText("Password must be at least 8 characters"),
    ).toBeVisible();
  });

  // ─── Happy path ───────────────────────────────────────────────────────────

  test("redirects to /dashboard on successful login", async ({ page }) => {
    // Mock the API route to return a successful response
    await page.route("/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          token: "mock-jwt-token",
          user: { id: "1", email: "demo@example.com", name: "Demo User" },
        }),
      });
    });

    await page.getByLabel("Email").fill("demo@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    await page.waitForURL("/dashboard");
    expect(page.url()).toContain("/dashboard");
  });

  test("stores token in localStorage on successful login", async ({ page }) => {
    await page.route("/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          token: "mock-jwt-token",
          user: { id: "1", email: "demo@example.com", name: "Demo User" },
        }),
      });
    });

    await page.getByLabel("Email").fill("demo@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    const token = await page.evaluate(() => localStorage.getItem("auth_token"));
    expect(token).toBe("mock-jwt-token");
  });

  // ─── API error ────────────────────────────────────────────────────────────

  test("shows error message on invalid credentials", async ({ page }) => {
    await page.route("/api/auth/login", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ message: "Invalid email or password" }),
      });
    });

    await page.getByLabel("Email").fill("wrong@example.com");
    await page.getByLabel("Password").fill("wrongpassword");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByRole("alert")).toContainText(
      "Invalid email or password",
    );
  });

  test("shows generic error on server failure", async ({ page }) => {
    await page.route("/api/auth/login", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ message: "Internal server error" }),
      });
    });

    await page.getByLabel("Email").fill("user@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByRole("alert")).toBeVisible();
  });

  // ─── Loading state ────────────────────────────────────────────────────────

  test("shows loading spinner while submitting", async ({ page }) => {
    // Delay the response so we can observe the loading state
    await page.route("/api/auth/login", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          token: "mock-jwt-token",
          user: { id: "1", email: "demo@example.com", name: "Demo User" },
        }),
      });
    });

    await page.getByLabel("Email").fill("demo@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();

    // Button should show loading text and be disabled
    await expect(
      page.getByRole("button", { name: /signing in/i }),
    ).toBeDisabled();
  });

  // ─── Accessibility ────────────────────────────────────────────────────────

  test("form has accessible labels and structure", async ({ page }) => {
    // Inputs are associated with labels
    const emailInput = page.getByLabel("Email");
    const passwordInput = page.getByLabel("Password");

    await expect(emailInput).toHaveAttribute("type", "email");
    await expect(passwordInput).toHaveAttribute("type", "password");

    // Form has accessible name
    await expect(page.getByRole("form", { name: "Login form" })).toBeVisible();
  });

  test("can submit form using keyboard only", async ({ page }) => {
    await page.route("/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          token: "mock-jwt-token",
          user: { id: "1", email: "demo@example.com", name: "Demo User" },
        }),
      });
    });

    // Tab to email, fill, tab to password, fill, tab to button, enter
    await page.getByLabel("Email").focus();
    await page.keyboard.type("demo@example.com");
    await page.keyboard.press("Tab");
    await page.keyboard.type("password123");
    await page.keyboard.press("Tab"); // forgot password link
    await page.keyboard.press("Tab"); // submit button
    await page.keyboard.press("Enter");

    await page.waitForURL("/dashboard");
  });
});
