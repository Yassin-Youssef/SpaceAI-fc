import { useEffect, useRef, useState } from "react";
import { animate, useReducedMotion } from "motion/react";

interface AnimatedNumberProps {
  value: number;
  /** Decimal places to display. */
  decimals?: number;
  /** Text appended after the number, e.g. "%". */
  suffix?: string;
  prefix?: string;
  duration?: number;
  className?: string;
}

/**
 * Smoothly counts from the previous value to the new one.
 * Respects the user's reduced-motion preference.
 */
export function AnimatedNumber({
  value,
  decimals = 0,
  suffix = "",
  prefix = "",
  duration = 1.1,
  className,
}: AnimatedNumberProps) {
  const reduce = useReducedMotion();
  const [display, setDisplay] = useState(reduce ? value : 0);
  const previous = useRef(reduce ? value : 0);

  useEffect(() => {
    if (reduce) {
      setDisplay(value);
      previous.current = value;
      return;
    }
    const controls = animate(previous.current, value, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setDisplay(v),
      onComplete: () => {
        previous.current = value;
      },
    });
    return () => controls.stop();
  }, [value, duration, reduce]);

  const text = Number.isFinite(display) ? display.toFixed(decimals) : "–";
  return (
    <span className={className} style={{ fontVariantNumeric: "tabular-nums" }}>
      {prefix}
      {text}
      {suffix}
    </span>
  );
}
