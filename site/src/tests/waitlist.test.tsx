/**
 * The waitlist form, from the page's side (spec 006 §3.5, AC9).
 *
 * The zero-free-text principle, carried from the product into marketing: the
 * email is the only thing anyone types, and the one question that matters — what
 * phone does your parent use — is three fixed choices, because it exists to
 * decide Wave 2 platform priority with data rather than with a text box nobody
 * can count.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Waitlist } from "@/sections/Waitlist";
import { WAITLIST_ERROR, WAITLIST_SUCCESS } from "@/copy";

afterEach(() => {
  vi.unstubAllGlobals();
});

function fill() {
  fireEvent.change(screen.getByLabelText(/your email/i), {
    target: { value: "child@example.com" },
  });
}

describe("the form's shape", () => {
  it("types the email, one optional note, and nothing else", () => {
    // The zero-free-text principle held until the beta conversion added one
    // deliberate exception (QUESTIONS 129): "what would you most like Kettle
    // to help with?" — optional, never required, capped server-side. The
    // email stays the only *required* typing, and this pin keeps the form
    // from growing a third field quietly.
    render(<Waitlist />);
    const typed = Array.from(
      screen.getByTestId("waitlist-form").querySelectorAll("input, textarea"),
    ).filter((el) =>
      ["text", "email", "search", "url", "textarea"].includes((el as HTMLInputElement).type),
    );

    expect(typed.map((el) => (el as HTMLInputElement).name)).toEqual([
      "email",
      "help_with",
      "company",
    ]);
    const note = typed[1] as HTMLTextAreaElement;
    expect(note.tagName).toBe("TEXTAREA");
    expect(note.required).toBe(false);
    expect((typed[0] as HTMLInputElement).required).toBe(true);
    expect(screen.queryByRole("textbox", { name: /phone/i })).toBeNull();
  });

  it("reassures under the button, in the approved words", () => {
    render(<Waitlist />);
    expect(screen.getByTestId("waitlist-reassure").textContent).toBe(
      "A short conversation. No commitment.",
    );
  });

  it("asks the platform question as three fixed choices", () => {
    render(<Waitlist />);
    const radios = screen.getAllByRole("radio") as HTMLInputElement[];
    expect(radios.map((r) => r.value)).toEqual(["iphone", "android", "unsure"]);
    expect(radios.every((r) => r.name === "parent_phone")).toBe(true);
  });

  it("hides the honeypot from people and from screen readers", () => {
    render(<Waitlist />);
    const honeypot = screen.getByTestId("honeypot");
    expect(honeypot).toHaveAttribute("aria-hidden", "true");
    expect(honeypot).toHaveAttribute("tabindex", "-1");
    expect(honeypot.className).toContain("hidden");
  });
});

describe("AC9 — it degrades to a plain POST", () => {
  it("carries a real action and method in the static markup", () => {
    const html = renderToStaticMarkup(<Waitlist />);
    expect(html).toMatch(/method="post"/);
    expect(html).toMatch(/action="https?:\/\/[^"]+\/waitlist"/);
  });
});

describe("submitting", () => {
  it("shows the flat success state, and stops showing the form", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    render(<Waitlist />);
    fill();
    fireEvent.submit(screen.getByTestId("waitlist-form"));

    await waitFor(() => expect(screen.getByTestId("waitlist-success")).toBeInTheDocument());
    expect(screen.getByTestId("waitlist-success").textContent).toBe(WAITLIST_SUCCESS);
    expect(screen.queryByTestId("waitlist-form")).toBeNull();
  });

  it("sends the honeypot along so the server can discard it", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);
    render(<Waitlist />);
    fill();
    fireEvent.submit(screen.getByTestId("waitlist-form"));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(Object.keys(body).sort()).toEqual(["company", "email", "help_with", "parent_phone"]);
    expect(body.email).toBe("child@example.com");
  });

  it("carries the optional note when one was written", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);
    render(<Waitlist />);
    fill();
    fireEvent.change(screen.getByLabelText(/most like Kettle to help with/i), {
      target: { value: "The mornings, mostly." },
    });
    fireEvent.submit(screen.getByTestId("waitlist-form"));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).help_with).toBe("The mornings, mostly.");
  });

  it("shows the page's only red, inline, when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<Waitlist />);
    fill();
    fireEvent.submit(screen.getByTestId("waitlist-form"));

    await waitFor(() => expect(screen.getByTestId("waitlist-error")).toBeInTheDocument());
    const error = screen.getByTestId("waitlist-error");
    expect(error.textContent).toBe(WAITLIST_ERROR);
    expect(error.className).toContain("text-error");
    // Still inside the form, next to the field it is about.
    expect(screen.getByTestId("waitlist-form").contains(error)).toBe(true);
  });

  it("treats a rejected submission as a failure rather than a success", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));
    render(<Waitlist />);
    fill();
    fireEvent.submit(screen.getByTestId("waitlist-form"));

    await waitFor(() => expect(screen.getByTestId("waitlist-error")).toBeInTheDocument());
    expect(screen.queryByTestId("waitlist-success")).toBeNull();
  });
});
