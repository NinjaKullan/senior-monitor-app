/**
 * The app's one action vocabulary (DECISIONS 324): three variants and no
 * others. `primary` is the filled pill, at most one per card; `secondary`
 * the outlined pill, same height and radius, for the next most likely tap;
 * `quiet` a text action in the accent colour with an underline, on the
 * surrounding text's baseline, still 44 px tall to the touch. All three:
 * 44 px minimum, a visible focus ring, reduced opacity when disabled. The
 * styles live in kettle.css under `.kt-action`; nothing here is inline, so
 * a screen cannot quietly grow a fourth style.
 */
import * as React from "react";

export type ActionVariant = "primary" | "secondary" | "quiet";

type Common = {
  variant: ActionVariant;
  className?: string;
};

export type ActionButtonProps = Common &
  Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "className"> & { href?: undefined };
export type ActionLinkProps = Common &
  Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, "className"> & { href: string };

function classes(variant: ActionVariant, className?: string): string {
  return ["kt-action", `kt-action-${variant}`, className].filter(Boolean).join(" ");
}

/** A button by default; an anchor when `href` is given (the Call pill). */
export function Action(props: ActionButtonProps | ActionLinkProps) {
  if (props.href !== undefined) {
    const { variant, className, ...rest } = props as ActionLinkProps;
    return <a data-variant={variant} className={classes(variant, className)} {...rest} />;
  }
  const { variant, className, type, ...rest } = props as ActionButtonProps;
  return (
    <button
      data-variant={variant}
      type={type ?? "button"}
      className={classes(variant, className)}
      {...rest}
    />
  );
}
