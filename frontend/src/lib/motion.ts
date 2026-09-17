/**
 * SpaceAI FC — shared motion presets
 * ===================================
 * One place for the timing curves used across pages so the product
 * feels consistent.  Built on `motion/react` (framer-motion's successor).
 */

import type { Transition, Variants } from "motion/react";

export const EASE_OUT: [number, number, number, number] = [0.22, 1, 0.36, 1];

export const springSoft: Transition = { type: "spring", stiffness: 260, damping: 26 };
export const springSnappy: Transition = { type: "spring", stiffness: 420, damping: 30 };

/** Page-level enter/exit used by the App-level AnimatePresence. */
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.32, ease: EASE_OUT } },
  // pointerEvents none stops clicks landing on a page that is animating out
  exit: { opacity: 0, y: -8, pointerEvents: "none", transition: { duration: 0.15, ease: "easeIn" } },
};

/** Parent container that staggers its children. */
export const staggerContainer = (stagger = 0.06, delay = 0.05): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren: stagger, delayChildren: delay } },
});

/** Child item for `staggerContainer`. */
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: EASE_OUT } },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.3 } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.94 },
  show: { opacity: 1, scale: 1, transition: { duration: 0.3, ease: EASE_OUT } },
};

/** Micro-interaction for buttons and clickable cards. */
export const pressable = {
  whileHover: { scale: 1.02 },
  whileTap: { scale: 0.97 },
  transition: springSnappy,
};

export const cardHover = {
  whileHover: { y: -3 },
  transition: springSoft,
};
