import { Info, Github, Keyboard, Video, FileUp } from "lucide-react";
import { useRef, type ReactNode } from "react";
import { Page, PageHeader, Button } from "./common/Primitives";
import { PipelineFlow } from "./common/PipelineFlow";
import { GITHUB_URL, PHASES } from "../../lib/project";

const INPUTS = [
  { icon: Keyboard, name: "Manual entry", text: "Type each player's number and pitch coordinates (x 0–120, y 0–80) and the passes as passer→receiver. A live pitch preview updates as you type." },
  { icon: Video, name: "Video or YouTube", text: "YOLOv8 detects players frame by frame, jersey colours split them into teams, and a homography maps them onto the pitch. A bundled corner-kick clip lets you try it without uploading anything." },
  { icon: FileUp, name: "Dataset", text: "Upload a CSV or JSON file with team, name, number, x, y and position columns, plus optional passes. Download a template from the Dataset tab to see the format." },
];

export function About({ onFeatureClick }: { onFeatureClick: (id: string) => void }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  return (
    <Page width="max-w-6xl" scrollRef={scrollRef}>
      <PageHeader
        title="How it works"
        description="What goes in, what each part of the engine does with it, and where the answers come from."
        actions={
          <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="press inline-flex h-10 items-center gap-2 rounded-md border border-line-strong bg-surface-2 px-4 text-sm font-semibold text-text-primary hover:bg-surface-3">
            <Github className="h-4 w-4" /> Source
          </a>
        }
      />

      <Block title="The loop">
        <PipelineFlow container={scrollRef} />
      </Block>

      <Block title="Three ways in" text="Video and dataset uploads are resolved to player positions first, then analysed exactly like manual entry.">
        <ul className="divide-y divide-line border-y border-line">
          {INPUTS.map((i) => (
            <li key={i.name} className="flex gap-4 py-5">
              <i.icon className="mt-1 h-5 w-5 shrink-0 text-section" strokeWidth={1.75} />
              <div>
                <h3 className="text-xl text-text-primary">{i.name}</h3>
                <p className="mt-1 text-sm text-text-secondary sm:text-base">{i.text}</p>
              </div>
            </li>
          ))}
        </ul>
      </Block>

      <Block title="Inside the engine" text="Four phases of stateless Python modules. Each one's output feeds the next.">
        <ol className="divide-y divide-line border-y border-line">
          {PHASES.map((p, i) => (
            <li key={p.name} className="grid grid-cols-[2.5rem_minmax(0,1fr)] gap-4 py-5">
              <span className="font-display text-4xl font-semibold leading-none text-text-muted">{i + 1}</span>
              <div className="min-w-0">
                <h3 className="text-xl text-text-primary">{p.name}</h3>
                <p className="mt-1 text-sm text-text-secondary sm:text-base">{p.text}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {p.modules.map((m) => <code key={m} className="rounded-sm bg-surface-2 px-1.5 py-0.5 text-xs text-text-secondary">{m}.py</code>)}
                </div>
              </div>
            </li>
          ))}
        </ol>
      </Block>

      <Block title="Where the words come from">
        <div className="space-y-3 text-sm text-text-secondary sm:text-base">
          <p>
            Reports, scouting notes and chat answers try OpenRouter first, then Anthropic, using whichever key the
            backend has. With neither, they fall back to templates filled from the knowledge graph, so every feature
            works with no key at all. The page always says which source wrote what you are reading.
          </p>
          <p>The numbers never come from a language model. Formations, control percentages, scores and patterns are computed by the engine.</p>
        </div>
      </Block>

      <Block title="Demo match data">
        <div className="space-y-3 text-sm text-text-secondary sm:text-base">
          <p>
            The bundled fixtures (2022 World Cup final, 2005 and 2011 Champions League finals, the 2017 Clásico)
            are built from{" "}
            <a href="https://github.com/statsbomb/open-data" target="_blank" rel="noreferrer" className="text-section underline-offset-4 hover:underline">StatsBomb open data</a>:
            each starter's position is their median event location and the passes are the real events. Data © StatsBomb,
            used under their non-commercial open-data licence with attribution. Two fixtures without public event data
            (Barcelona 4-3 Real Madrid 2025, Liverpool 7-0 Manchester United 2023) use real line-ups and scores with
            synthesised passes, and are labelled "reconstructed" wherever they appear.
          </p>
          <p>
            Player Assessment uses ten real stat lines (Messi, Mbappé, Xavi, Gerrard, Kaká and others) counted from
            those events and normalised per 90 minutes. Distance covered and sprints are estimates, because event data
            carries no tracking. Simulation and Compare presets borrow each fixture's tactical identity; they are
            stylised what-ifs, not replays.
          </p>
        </div>
      </Block>

      <section className="mt-12 flex flex-col gap-5 border-t border-line pt-8 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="font-display text-2xl font-semibold text-text-primary">Built by Yassin Youssef</div>
          <p className="mt-1 text-sm text-text-secondary">Engine, API and interface, designed and written end to end.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="press inline-flex h-10 items-center gap-2 rounded-md border border-line-strong bg-surface-2 px-4 text-sm font-semibold text-text-primary hover:bg-surface-3">
            <Github className="h-4 w-4" /> Source on GitHub
          </a>
          <Button onClick={() => onFeatureClick("full-match")}>Run a full match analysis</Button>
        </div>
      </section>
    </Page>
  );
}

function Block({ title, text, children }: { title: string; text?: string; children: ReactNode }) {
  return (
    <section className="grid gap-6 border-b border-line py-12 last-of-type:border-b-0 lg:grid-cols-[minmax(0,1fr)_minmax(0,2.2fr)] lg:gap-10">
      <div>
        <h2 className="text-2xl text-text-primary sm:text-3xl">{title}</h2>
        {text && <p className="mt-2 text-sm text-text-secondary">{text}</p>}
      </div>
      <div className="min-w-0">{children}</div>
    </section>
  );
}
