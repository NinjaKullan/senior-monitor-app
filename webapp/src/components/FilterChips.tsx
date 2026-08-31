/**
 * One row of filter chips (spec 012 §9.1 and §9.3).
 *
 * A radiogroup rather than a row of buttons, because that is what it is: one
 * of these is always chosen, and a screen reader should say so. The selected
 * chip carries the copper the rest of the app uses for "this one", and the
 * row wraps rather than scrolling sideways — a filter you have to swipe to
 * reach is a filter nobody uses.
 */
export interface ChipOption {
  id: string;
  label: string;
}

const CHIP: React.CSSProperties = {
  border: "1px solid var(--hair)",
  borderRadius: "999px",
  padding: "0.4375rem 0.8125rem",
  fontSize: "0.8125rem",
  background: "var(--card)",
  color: "var(--inkmid)",
  cursor: "pointer",
  minHeight: "2.25rem",
};

const CHOSEN: React.CSSProperties = {
  ...CHIP,
  border: "1px solid var(--copperbd)",
  background: "var(--coppertint)",
  color: "var(--copperdeep)",
  fontWeight: 600,
};

export function FilterChips({
  groupLabel,
  options,
  selected,
  onSelect,
  testId,
}: {
  groupLabel: string;
  options: ChipOption[];
  selected: string;
  onSelect: (id: string) => void;
  testId: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={groupLabel}
      style={{ display: "flex", gap: "0.375rem", flexWrap: "wrap" }}
      data-testid={testId}
    >
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          role="radio"
          aria-checked={option.id === selected}
          onClick={() => onSelect(option.id)}
          style={option.id === selected ? CHOSEN : CHIP}
          data-testid={`${testId}-option`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
