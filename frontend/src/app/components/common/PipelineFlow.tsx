import { motion, useReducedMotion, useScroll, useSpring, useTransform, type MotionValue } from "motion/react";
import { useRef, type RefObject } from "react";
import { PIPELINE, type PipelineStep } from "../../../lib/project";
import { sectionVar } from "../../../lib/features";

/**
 * Sense → Understand → Reason → Act → Explain as a flow diagram.
 * The connecting line fills as the diagram scrolls through the viewport,
 * and each step lights up in its area's colour as the line reaches it.
 */
export function PipelineFlow({ container }: { container: RefObject<HTMLElement | null> }) {
  const ref = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({ container, target: ref, offset: ["start 85%", "end 55%"] });
  const smooth = useSpring(scrollYProgress, { stiffness: 220, damping: 32, restDelta: 0.001 });
  const progress = reduce ? scrollYProgress : smooth;
  const fill = useTransform(progress, (v) => (reduce ? 1 : v));

  return (
    <div ref={ref} className="relative">
      {/* Track + fill: horizontal from md up, vertical below */}
      <div className="absolute left-[19px] top-5 bottom-5 w-px bg-line-strong md:left-[10%] md:right-[10%] md:top-[19px] md:bottom-auto md:h-px md:w-auto" aria-hidden>
        <motion.div className="h-full w-full origin-top bg-section-fill md:hidden" style={{ scaleY: fill }} />
        <motion.div className="hidden h-full w-full origin-left bg-section-fill md:block" style={{ scaleX: fill }} />
      </div>

      <ol className="relative grid gap-6 md:grid-cols-5 md:gap-4">
        {PIPELINE.map((step, i) => (
          <Step key={step.name} step={step} index={i} progress={fill} />
        ))}
      </ol>
    </div>
  );
}

function Step({ step, index, progress }: { step: PipelineStep; index: number; progress: MotionValue<number> }) {
  const at = index / (PIPELINE.length - 1);
  const lit = useTransform(progress, [Math.max(0, at - 0.12), at], [0, 1]);
  const Icon = step.icon;
  return (
    <li className="flex gap-4 md:flex-col md:items-center md:gap-3 md:text-center" style={sectionVar(step.section)}>
      <div className="relative h-10 w-10 shrink-0">
        <div className="absolute inset-0 flex items-center justify-center rounded-sm border border-line-strong bg-surface-1 text-text-muted">
          <Icon className="h-[18px] w-[18px]" strokeWidth={1.75} />
        </div>
        <motion.div style={{ opacity: lit }} className="absolute inset-0 flex items-center justify-center rounded-sm border border-section bg-surface-2 text-section">
          <Icon className="h-[18px] w-[18px]" strokeWidth={1.75} />
        </motion.div>
      </div>
      <div className="min-w-0 pt-1 md:pt-0">
        <div className="font-display text-xl font-semibold text-text-primary">{step.name}</div>
        <p className="mt-0.5 text-sm text-text-secondary md:mx-auto md:max-w-[22ch]">{step.text}</p>
      </div>
    </li>
  );
}
