/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
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
import {
  LOGIN_BUTTON,
  LOGIN_CODE_BUTTON,
  LOGIN_CODE_LABEL,
  LOGIN_CODE_RESEND,
  LOGIN_CODE_WRONG,
  LOGIN_FAILED,
  LOGIN_RATE_LIMITED,
  LOGIN_SENT,
} from "@/lib/copy";

const noVerify = vi.fn().mockResolvedValue(undefined);

function mount(onSend: (email: string) => Promise<void>, onVerify = noVerify) {
  return render(<Login onSend={onSend} onVerify={onVerify} />);
}

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("Email address"), {
    target: { value: "child@example.com" },
  });
  fireEvent.submit(screen.getByRole("button").closest("form")!);
}

describe("the three outcomes a sender can have", () => {
  it("sets the expectation on success: a minute, and check spam", async () => {
    mount(vi.fn().mockResolvedValue(undefined));
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
    mount(vi.fn().mockRejectedValue(rateLimited));
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
    mount(vi.fn().mockRejectedValue(shaped));
    fillAndSubmit();

    await waitFor(() =>
      expect(screen.getByTestId("login-error").textContent).toBe(LOGIN_RATE_LIMITED),
    );
  });

  it("words any other failure too, generically", async () => {
    mount(vi.fn().mockRejectedValue(new Error("offline")));
    fillAndSubmit();

    await waitFor(() => expect(screen.getByTestId("login-error")).toBeInTheDocument());
    expect(screen.getByTestId("login-error").textContent).toBe(LOGIN_FAILED);
  });

  it("clears a shown error on a later successful send", async () => {
    const send = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(undefined);
    mount(send);

    fillAndSubmit();
    await waitFor(() => expect(screen.getByTestId("login-error")).toBeInTheDocument());
    fillAndSubmit();
    await waitFor(() => expect(screen.getByTestId("login-sent")).toBeInTheDocument());
    expect(screen.queryByTestId("login-error")).toBeNull();
  });

  it("keeps the error copy calm — no red class, no alarm vocabulary", () => {
    // The mailer is equipment. Nothing in this app earns red, and a login
    // hiccup is not going to be the first thing that does.
    for (const copy of [LOGIN_RATE_LIMITED, LOGIN_FAILED, LOGIN_SENT, LOGIN_CODE_WRONG]) {
      expect(copy.toLowerCase()).not.toMatch(/error|fail|broken|wrong|urgent|alert/);
    }
    mount(vi.fn().mockRejectedValue(new Error("x")));
    fillAndSubmit();
    return waitFor(() => {
      expect(screen.getByTestId("login-error").className).not.toMatch(/red|destructive|error/);
    });
  });
});

describe("the wiring layer the field bug lived in", () => {
  it("sendSignInCode throws the error supabase-js only returns", async () => {
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
    const { sendSignInCode } = await import("@/lib/data");
    await expect(sendSignInCode("child@example.com")).rejects.toBe(limit);
    vi.doUnmock("@/lib/supabase");
  });
});

/**
 * Spec 013 §5 — the second step, and the reason it exists.
 *
 * A link tapped in a phone's mail app opens in that app's browser, so the
 * session is created where the installed Kettle cannot see it and the family
 * concludes the product is broken. The code is the fix, so what these pin is
 * mostly about a person holding a phone: the field has to invite the OS to
 * offer the digits, a mistyped code has to say something different from a dead
 * mailer, and asking for a new code must never cost the family the code they
 * already have.
 */
describe("the code step", () => {
  async function reachStep2(onVerify = noVerify) {
    mount(vi.fn().mockResolvedValue(undefined), onVerify);
    fillAndSubmit();
    await waitFor(() => expect(screen.getByTestId("login-code")).toBeInTheDocument());
  }

  function typeCode(value: string) {
    fireEvent.change(screen.getByTestId("login-code"), { target: { value } });
    fireEvent.submit(screen.getByTestId("login-code").closest("form")!);
  }

  it("stays hidden until a send has actually succeeded", async () => {
    mount(vi.fn().mockRejectedValue(new Error("offline")));
    expect(screen.queryByTestId("login-code")).toBeNull();
    fillAndSubmit();
    // A failed send must not reveal it either: a code field over an email that
    // was never sent is the same lie DECISIONS 115 was filed about.
    await waitFor(() => expect(screen.getByTestId("login-error")).toBeInTheDocument());
    expect(screen.queryByTestId("login-code")).toBeNull();
  });

  it("invites the phone to offer the code, and says what it wants", async () => {
    await reachStep2();
    const field = screen.getByTestId("login-code");
    // `one-time-code` is what makes iOS surface the digits from Mail; without
    // it the family retypes them by hand and the code path loses its advantage.
    expect(field).toHaveAttribute("autocomplete", "one-time-code");
    expect(field).toHaveAttribute("inputmode", "numeric");
    expect(field).toHaveAttribute("placeholder", "000000");
    expect(field).toHaveAttribute("aria-label", LOGIN_CODE_LABEL);
    expect(screen.getByTestId("login-sent").textContent).toBe(LOGIN_SENT);
  });

  it("verifies with the address and the typed code, in the shape supabase wants", async () => {
    const verify = vi.fn().mockResolvedValue(undefined);
    await reachStep2(verify);
    typeCode("123456");
    await waitFor(() => expect(verify).toHaveBeenCalledTimes(1));
    expect(verify).toHaveBeenCalledWith("child@example.com", "123456");
  });

  it("says a wrong or expired code in its own words, not the generic ones", async () => {
    // The exact shape Supabase returns: a 403 whose message is prose.
    const bad = Object.assign(new Error("Token has expired or is invalid"), { status: 403 });
    await reachStep2(vi.fn().mockRejectedValue(bad));
    typeCode("000000");
    await waitFor(() => expect(screen.getByTestId("login-error")).toBeInTheDocument());
    expect(screen.getByTestId("login-error").textContent).toBe(LOGIN_CODE_WRONG);
    // Still on step 2: the next step is retyping, so the field must stay.
    expect(screen.getByTestId("login-code")).toBeInTheDocument();
  });

  it("falls back to the generic failure for anything it does not recognise", async () => {
    await reachStep2(vi.fn().mockRejectedValue(new Error("offline")));
    typeCode("123456");
    await waitFor(() => expect(screen.getByTestId("login-error")).toBeInTheDocument());
    expect(screen.getByTestId("login-error").textContent).toBe(LOGIN_FAILED);
  });

  it("resends to the same address, and keeps the code field when the mailer says wait", async () => {
    const send = vi
      .fn()
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(
        Object.assign(new Error("rate limit"), {
          status: 429,
          code: "over_email_send_rate_limit",
        }),
      );
    mount(send, noVerify);
    fillAndSubmit();
    await waitFor(() => expect(screen.getByTestId("login-code")).toBeInTheDocument());

    fireEvent.click(screen.getByTestId("login-resend"));
    await waitFor(() => expect(send).toHaveBeenCalledTimes(2));
    expect(send).toHaveBeenLastCalledWith("child@example.com");

    // The mailer's 60-second minimum is a real answer and is said out loud.
    await waitFor(() =>
      expect(screen.getByTestId("login-send-error").textContent).toBe(LOGIN_RATE_LIMITED),
    );
    // And the family keeps the code they may already be holding: collapsing
    // back to step 1 here would throw away a perfectly good code and a typed
    // one with it.
    expect(screen.getByTestId("login-code")).toBeInTheDocument();
  });

  it("carries the ruled button and link words, verbatim", async () => {
    expect(LOGIN_BUTTON).toBe("Email me a code");
    expect(LOGIN_CODE_LABEL).toBe("6-digit code");
    expect(LOGIN_CODE_BUTTON).toBe("Sign in");
    expect(LOGIN_CODE_RESEND).toBe("Send a new code");
    await reachStep2();
    expect(screen.getByTestId("login-resend").textContent).toBe(LOGIN_CODE_RESEND);
    expect(screen.getByRole("button", { name: LOGIN_CODE_BUTTON })).toBeInTheDocument();
  });
});

describe("the verify wiring", () => {
  it("verifySignInCode throws, and asks supabase for the email OTP type", async () => {
    vi.resetModules();
    const bad = Object.assign(new Error("Token has expired or is invalid"), { status: 403 });
    const verifyOtp = vi.fn().mockResolvedValue({ error: bad });
    vi.doMock("@/lib/supabase", () => ({ supabase: { auth: { verifyOtp } } }));
    const { verifySignInCode } = await import("@/lib/data");
    await expect(verifySignInCode("child@example.com", "123456")).rejects.toBe(bad);
    expect(verifyOtp).toHaveBeenCalledWith({
      email: "child@example.com",
      token: "123456",
      type: "email",
    });
    vi.doUnmock("@/lib/supabase");
  });
});
