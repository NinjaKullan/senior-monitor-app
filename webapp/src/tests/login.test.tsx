/**
 * DECISIONS 115 — login failures surface as words, not silence.
 *
 * The regression this guards is exact and field-proven: the built-in mailer
 * rate-limits at roughly two emails an hour, supabase-js *returns* the 429
 * rather than throwing it, and this screen said "check your email" over a link
 * that was never sent. A stranger's family hits that on their second login
 * attempt and concludes the product is broken.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Login } from "@/screens/Login";
import { LOGIN_FAILED, LOGIN_RATE_LIMITED, LOGIN_SENT } from "@/lib/copy";

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: "child@example.com" },
  });
  fireEvent.submit(screen.getByRole("button").closest("form")!);
}

describe("the three outcomes a sender can have", () => {
  it("sets the expectation on success: a minute, and check spam", async () => {
    render(<Login onSend={vi.fn().mockResolvedValue(undefined)} />);
    fillAndSubmit();

    await waitFor(() => expect(screen.getByTestId("login-sent")).toBeInTheDocument());
    expect(screen.getByTestId("login-sent").textContent).toBe(LOGIN_SENT);
    expect(LOGIN_SENT).toContain("spam");
  });

  it("says the rate limit out loud, and keeps the form there for the retry", async () => {
    // The exact shape supabase-js returns for the built-in mailer's limit.
    const rateLimited = Object.assign(new Error("rate limit"), {
      status: 429,
      code: "over_email_send_rate_limit",
    });
    render(<Login onSend={vi.fn().mockRejectedValue(rateLimited)} />);
    fillAndSubmit();

    await waitFor(() => expect(screen.getByTestId("login-error")).toBeInTheDocument());
    const error = screen.getByTestId("login-error");
    expect(error.textContent).toBe(LOGIN_RATE_LIMITED);
    expect(error).toHaveAttribute("role", "alert");
    // Not "sent", and the form is still on screen — waiting is the fix, and the
    // screen must not pretend a link is on its way.
    expect(screen.queryByTestId("login-sent")).toBeNull();
    expect(screen.getByLabelText("Email address")).toBeInTheDocument();
  });

  it("recognises the limit by code alone when no status arrives", async () => {
    const shaped = Object.assign(new Error("limit"), { code: "over_email_send_rate_limit" });
    render(<Login onSend={vi.fn().mockRejectedValue(shaped)} />);
    fillAndSubmit();

    await waitFor(() =>
      expect(screen.getByTestId("login-error").textContent).toBe(LOGIN_RATE_LIMITED),
    );
  });

  it("words any other failure too, generically", async () => {
    render(<Login onSend={vi.fn().mockRejectedValue(new Error("offline"))} />);
    fillAndSubmit();

    await waitFor(() => expect(screen.getByTestId("login-error")).toBeInTheDocument());
    expect(screen.getByTestId("login-error").textContent).toBe(LOGIN_FAILED);
  });

  it("clears a shown error on a later successful send", async () => {
    const send = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(undefined);
    render(<Login onSend={send} />);

    fillAndSubmit();
    await waitFor(() => expect(screen.getByTestId("login-error")).toBeInTheDocument());
    fillAndSubmit();
    await waitFor(() => expect(screen.getByTestId("login-sent")).toBeInTheDocument());
    expect(screen.queryByTestId("login-error")).toBeNull();
  });

  it("keeps the error copy calm — no red class, no alarm vocabulary", () => {
    // The mailer is equipment. Nothing in this app earns red, and a login
    // hiccup is not going to be the first thing that does.
    for (const copy of [LOGIN_RATE_LIMITED, LOGIN_FAILED, LOGIN_SENT]) {
      expect(copy.toLowerCase()).not.toMatch(/error|fail|broken|wrong|urgent|alert/);
    }
    render(<Login onSend={vi.fn().mockRejectedValue(new Error("x"))} />);
    fillAndSubmit();
    return waitFor(() => {
      expect(screen.getByTestId("login-error").className).not.toMatch(/red|destructive|error/);
    });
  });
});

describe("the wiring layer the field bug lived in", () => {
  it("sendMagicLink throws the error supabase-js only returns", async () => {
    // The original bug was not in the Login component at all: supabase-js
    // hands errors back as values, and the call site discarded them. This
    // pins the translation from returned-error to thrown-error.
    vi.resetModules();
    const limit = Object.assign(new Error("429"), {
      status: 429,
      code: "over_email_send_rate_limit",
    });
    vi.doMock("@/lib/supabase", () => ({
      supabase: { auth: { signInWithOtp: vi.fn().mockResolvedValue({ error: limit }) } },
    }));
    const { sendMagicLink } = await import("@/lib/data");
    await expect(sendMagicLink("child@example.com")).rejects.toBe(limit);
    vi.doUnmock("@/lib/supabase");
  });
});
