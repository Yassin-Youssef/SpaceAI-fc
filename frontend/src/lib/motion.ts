/**
 * SpaceAI FC — shared motion presets
 * ===================================
 * One place for curves and springs so the product moves with one voice.
 * Built on `motion/react` (framer-motion's successor). The matching CSS
 * curves live in styles/theme.css as --ease-out / --ease-in-out.
 *
 * Rules the presets encode: entrances ease out, exits are shorter than
 * entrances, nothing UI-level runs longer than ~500ms, stagger stays
 * between 30 and 80ms.
 */

import type { Transition, Variants } from "motion/react";

export const EASE_OUT: [number, number, number, number] = [0.23, 1, 0.32, 1];
export const EASE_IN_OUT: [number, number, number, number] = [0.77, 0, 0.175, 1];

/** Page-level spring: settles in ~350ms with no visible overshoot. */
export const springPage: Transition = { type: "spring", stiffness: 300, damping: 30 };
/** Indicators and toggles that slide between positions. */
export const springSoft: Transition = { type: "spring", stiffness: 420, damping: 36 };
/** Press feedback: ~150ms. */
export const springPress: Transition = { type: "spring", stiffness: 600, damping: 32 };

/** Page enter/exit used by the App-level AnimatePresence (mode="wait"). */
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: springPage },
  // pointerEvents none stops clicks landing on a page that is animating out
  exit: { opacity: 0, pointerEvents: "none", transition: { duration: 0.2, ease: EASE_OUT } },
};

/** Parent container that staggers its children. */
export const staggerContainer = (stagger = 0.05, delay = 0): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren: stagger, delayChildren: delay } },
});

/** Child item for `staggerContainer`. */
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: EASE_OUT } },
};

/** Content replacing a skeleton: a crossfade, not a pop. */
export const crossfade: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.25, ease: EASE_OUT } },
  exit: { opacity: 0, transition: { duration: 0.15, ease: EASE_OUT } },
};

/** Section reveal on scroll (used with whileInView, once). */
export const reveal: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: EASE_OUT } },
};

/** Press feedback for motion buttons. Hover styling stays in CSS. */
export const pressable = {
  whileTap: { scale: 0.98 },
  transition: springPress,
};
