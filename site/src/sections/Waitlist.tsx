import { useState } from "react";
import { Section } from "@/components/Section";
import { PillButton } from "@/components/Pill";
import {
  WAITLIST_ANDROID_LABEL,
  WAITLIST_BODY,
  WAITLIST_CTA,
  WAITLIST_EMAIL_LABEL,
  WAITLIST_ERROR,
  WAITLIST_H2,
  WAITLIST_HELP_LABEL,
  WAITLIST_IPHONE_LABEL,
  WAITLIST_PHONE_LABEL,
  WAITLIST_REASSURE_BODY,
  WAITLIST_SUCCESS,
  WAITLIST_UNSURE_LABEL,
} from "@/copy";

/** Where the form posts. Baked at build; the default is the production API. */
const ENDPOINT = `${import.meta.env.VITE_API_BASE_URL ?? "https://kettle-api.fly.dev"}/waitlist`;

/** The bot trap. Named for something a form-filler expects to find. */
const HONEYPOT = "company";

const CHOICES = [
  { value: "iphone", label: WAITLIST_IPHONE_LABEL },
  { value: "android", label: WAITLIST_ANDROID_LABEL },
  { value: "unsure", label: WAITLIST_UNSURE_LABEL },
] as const;

/**
 * The waitlist, and the one question this page exists to ask.
 *
 * "What phone does your parent use?" decides Wave 2 platform priority with data
 * rather than instinct, which is why it is three fixed choices and not a text
 * box — the zero-free-text principle from the product, extended to marketing.
 * The email is the only thing anyone types.
 *
 * The form has a real `action` and `method`, so with JavaScript off the browser
 * posts it straight to the API and the API answers in words (AC9). With
 * JavaScript on, the submit is intercepted only to keep the reader on the page.
 * Failure is the page's single use of red, and it is inline, next to the field.
 */
export function Waitlist() {
  const [state, setState] = useState<"idle" | "sent" | "failed">("idle");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          email: form.get("email"),
          parent_phone: form.get("parent_phone"),
          help_with: form.get("help_with"),
          [HONEYPOT]: form.get(HONEYPOT),
        }),
      });
      setState(response.ok ? "sent" : "failed");
    } catch {
      setState("failed");
    }
  }

  return (
    <Section id="waitlist">
      <h2 className="text-display font-light" data-testid="section-heading">
        {WAITLIST_H2}
      </h2>
      {/* Stated flat. No countdown, no "limited", no urgency vocabulary of any
          kind — the copy law bans the words, and the offer does not need them. */}
      <p className="max-w-xl text-body text-secondary">{WAITLIST_BODY}</p>

      {state === "sent" ? (
        <p className="text-lead" data-testid="waitlist-success">
          {WAITLIST_SUCCESS}
        </p>
      ) : (
        <form
          action={ENDPOINT}
          method="post"
          onSubmit={submit}
          className="flex max-w-md flex-col gap-6"
          data-testid="waitlist-form"
        >
          <label className="flex flex-col gap-2 text-body">
            {WAITLIST_EMAIL_LABEL}
            <input
              type="email"
              name="email"
              required
              autoComplete="email"
              className="rounded-full border border-ink/30 bg-transparent px-5 py-3 text-body
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
            />
          </label>

          <fieldset className="flex flex-col gap-3">
            <legend className="text-body">{WAITLIST_PHONE_LABEL}</legend>
            <div className="flex flex-wrap gap-4">
              {CHOICES.map((choice, index) => (
                <label key={choice.value} className="flex items-center gap-2 text-body">
                  <input
                    type="radio"
                    name="parent_phone"
                    value={choice.value}
                    defaultChecked={index === 0}
                    className="accent-calm"
                  />
                  {choice.label}
                </label>
              ))}
            </div>
          </fieldset>

          {/* The one free-text field, optional on purpose (QUESTIONS 129): a
              kindness, not a gate. The server strips, caps and stores absence
              for an empty answer; no maxLength attribute here because the
              digit walk reads perceivable attributes, and the cap is the
              API's job either way. */}
          <label className="flex flex-col gap-2 text-body">
            {WAITLIST_HELP_LABEL}
            {/* Height by class, not a rows attribute: the digit walk reads
                every perceivable attribute, and a numeral has no business
                being the reason one passes. */}
            <textarea
              name="help_with"
              className="min-h-24 rounded-card border border-ink/30 bg-transparent px-5 py-3
                text-body focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
            />
          </label>

          {/* Silently accepted and discarded server-side. Hidden from people and
              from screen readers; only a form-filler ever finds it. */}
          <input
            type="text"
            name={HONEYPOT}
            tabIndex={-1}
            autoComplete="off"
            aria-hidden="true"
            data-testid="honeypot"
            className="hidden"
          />

          <div>
            <PillButton>{WAITLIST_CTA}</PillButton>
            <p className="mt-3 text-body text-secondary" data-testid="waitlist-reassure">
              {WAITLIST_REASSURE_BODY}
            </p>
          </div>

          {state === "failed" && (
            <p role="alert" className="text-body text-error" data-testid="waitlist-error">
              {WAITLIST_ERROR}
            </p>
          )}
        </form>
      )}
    </Section>
  );
}
