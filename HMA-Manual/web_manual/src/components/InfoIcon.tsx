import { useEffect, useId, useRef, useState, type ReactNode } from "react";

type InfoIconProps = {
  children: ReactNode;
  /** Accessible name for the trigger button. */
  label?: string;
  /** Which way the tooltip extends from the icon. Default opens to the right. */
  align?: "left" | "center" | "right";
};

/**
 * Small "i" trigger that reveals explanatory copy on hover (desktop), focus
 * (keyboard), or tap (touch). Keeps helper prose off the page surface while
 * leaving it one gesture away. Inherits its icon color from the surrounding
 * text so it works on both light cards and the dark brand header.
 */
export function InfoIcon({ children, label = "More information", align = "left" }: InfoIconProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLSpanElement>(null);
  const tooltipId = useId();

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const positionClass =
    align === "right" ? "right-0" : align === "center" ? "left-1/2 -translate-x-1/2" : "left-0";

  return (
    <span className="relative inline-flex align-middle" ref={containerRef}>
      <button
        aria-describedby={open ? tooltipId : undefined}
        aria-expanded={open}
        aria-label={label}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-current text-[10px] font-bold leading-none opacity-50 transition hover:opacity-100 focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        onBlur={() => setOpen(false)}
        onClick={() => setOpen((value) => !value)}
        onFocus={() => setOpen(true)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        type="button"
      >
        i
      </button>
      {open ? (
        <span
          className={`absolute top-[calc(100%+6px)] z-30 w-64 max-w-[min(16rem,75vw)] rounded-xl border border-rim bg-panel px-3 py-2 text-left text-xs font-normal normal-case leading-relaxed tracking-normal text-ink/80 shadow-lg ${positionClass}`}
          id={tooltipId}
          role="tooltip"
        >
          {children}
        </span>
      ) : null}
    </span>
  );
}
