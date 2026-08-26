/**
 * The city picker (spec 010 §1): the ONE surface that moves a parent's
 * clock. Typing filters the curated list; only a PICKED entry ever commits —
 * free text reverts on blur, so no keystroke can write a zone. Clearing the
 * field clears the label only and never touches tz. The IANA name is never
 * rendered: options read "Dallas, United States".
 */

import { useRef, useState } from "react";
import { CityEntry, displayOf, searchCities } from "@/lib/cities";
import { CITY_ESCAPE_HATCH, CITY_FIELD_LABEL, CITY_PLACEHOLDER } from "@/lib/copy";

export function CityPicker({
  name,
  committed,
  onPick,
  onClear,
}: {
  /** The parent's display name, for the placeholder. */
  name: string;
  /** The committed city label ("" when unset). */
  committed: string;
  onPick: (entry: CityEntry) => void;
  onClear: () => void;
}) {
  const [text, setText] = useState(committed);
  const [open, setOpen] = useState(false);
  const picking = useRef(false);
  const results = open ? searchCities(text) : [];

  const settle = () => {
    if (picking.current) return;
    setOpen(false);
    if (text.trim() === "") {
      if (committed !== "") onClear();
      setText("");
      return;
    }
    // Free text cannot commit: anything unpicked reverts to what stands.
    setText(committed);
  };

  return (
    <div style={{ position: "relative", minWidth: "11rem" }} data-testid="city-picker">
      <input
        type="text"
        role="combobox"
        aria-expanded={open && results.length > 0}
        aria-label={CITY_FIELD_LABEL}
        placeholder={CITY_PLACEHOLDER.replace("{name}", name)}
        value={text}
        onChange={(event) => {
          setText(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={settle}
        onKeyDown={(event) => {
          // Enter on free text must not commit anything.
          if (event.key === "Enter") event.preventDefault();
          if (event.key === "Escape") setOpen(false);
        }}
        style={{
          border: "1px solid var(--hair)",
          borderRadius: "999px",
          padding: "0.5rem 0.875rem",
          fontSize: "0.8125rem",
          color: "var(--ink)",
          background: "var(--paper)",
          width: "100%",
          boxSizing: "border-box",
          minHeight: "2.75rem",
        }}
        data-testid="city-input"
      />
      {open && text.trim() !== "" && (
        <div
          role="listbox"
          style={{
            position: "absolute",
            zIndex: 30,
            top: "100%",
            left: 0,
            right: 0,
            marginTop: "0.25rem",
            background: "var(--card)",
            border: "1px solid var(--hair)",
            borderRadius: "0.875rem",
            overflow: "hidden",
            boxShadow: "0 6px 18px var(--hair)",
          }}
          data-testid="city-results"
        >
          {results.map((entry) => (
            <button
              key={displayOf(entry)}
              type="button"
              role="option"
              aria-selected={false}
              onMouseDown={() => {
                // Mousedown beats the input's blur, so a pick is never
                // swallowed by the revert.
                picking.current = true;
              }}
              onClick={() => {
                picking.current = false;
                setText(entry.city);
                setOpen(false);
                onPick(entry);
              }}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                background: "none",
                border: "none",
                padding: "0.5625rem 0.875rem",
                fontSize: "0.8125rem",
                color: "var(--ink)",
                cursor: "pointer",
                minHeight: "2.5rem",
              }}
              className="kt-rowbtn"
              data-testid="city-option"
            >
              {displayOf(entry)}
            </button>
          ))}
          <div
            style={{
              padding: "0.5rem 0.875rem 0.625rem",
              fontSize: "0.75rem",
              color: "var(--mute)",
              borderTop: results.length > 0 ? "1px solid var(--hair)" : "none",
            }}
            data-testid="city-escape"
          >
            {CITY_ESCAPE_HATCH}
          </div>
        </div>
      )}
    </div>
  );
}
