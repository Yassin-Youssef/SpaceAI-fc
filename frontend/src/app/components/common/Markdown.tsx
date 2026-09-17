import { Fragment, type ReactNode } from "react";

/**
 * Very small, safe Markdown-ish renderer for LLM / knowledge-graph answers.
 * Supports **bold**, *italic*, `code`, bullet lines and paragraphs.
 * No HTML is ever injected.
 */
export function Markdown({ text, className }: { text: string; className?: string }) {
  const blocks = text.replace(/\r\n/g, "\n").split(/\n{2,}/);
  return (
    <div className={className}>
      {blocks.map((block, bi) => {
        const lines = block.split("\n").filter((l) => l.trim().length > 0);
        if (lines.length === 0) return null;
        const isList = lines.every((l) => /^\s*([•\-*]|\d+[.)])\s+/.test(l));
        if (isList) {
          return (
            <ul key={bi} className="my-2 space-y-1.5 pl-1">
              {lines.map((l, li) => (
                <li key={li} className="flex gap-2">
                  <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                  <span>{inline(l.replace(/^\s*([•\-*]|\d+[.)])\s+/, ""))}</span>
                </li>
              ))}
            </ul>
          );
        }
        const heading = lines.length === 1 && /^#{1,3}\s+/.test(lines[0]);
        if (heading) {
          return (
            <h4 key={bi} className="mt-3 mb-1 font-bold text-white">
              {inline(lines[0].replace(/^#{1,3}\s+/, ""))}
            </h4>
          );
        }
        return (
          <p key={bi} className="my-2 leading-relaxed">
            {lines.map((l, li) => (
              <Fragment key={li}>
                {inline(l)}
                {li < lines.length - 1 && <br />}
              </Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\n]+\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(<strong key={k++} className="font-bold text-white">{tok.slice(2, -2)}</strong>);
    else if (tok.startsWith("`")) out.push(<code key={k++} className="rounded bg-white/10 px-1 py-0.5 text-[0.9em] text-brand">{tok.slice(1, -1)}</code>);
    else out.push(<em key={k++} className="text-text-secondary">{tok.slice(1, -1)}</em>);
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}
