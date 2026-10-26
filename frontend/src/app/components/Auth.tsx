import { motion, AnimatePresence } from "motion/react";
import { Mail, Lock, User, UserRound, AlertTriangle } from "lucide-react";
import { useMemo, useState } from "react";
import { signIn, signUp, signInWithGoogle, isSupabaseConfigured } from "../../lib/supabase";
import type { UserProfile } from "../../lib/types";
import { DEMO_TEAM_A, DEMO_TEAM_B, DEMO_PASSES, DEMO_TEAM_A_COLOR, DEMO_TEAM_B_COLOR } from "../../lib/demo";
import { toPlayerData } from "../../lib/api";
import { Button } from "./common/Primitives";
import { PitchPreview } from "./common/PitchPreview";
import { EASE_OUT } from "../../lib/motion";

interface AuthProps {
  onLogin: (user: UserProfile) => void;
  onGuest: () => void;
}

export function Auth({ onLogin, onGuest }: AuthProps) {
  const configured = isSupabaseConfigured();
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const teamA = useMemo(() => toPlayerData(DEMO_TEAM_A), []);
  const teamB = useMemo(() => toPlayerData(DEMO_TEAM_B), []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (isSignUp && name.trim().length < 2) { setError("Enter your name."); return; }
    if (isSignUp && password !== confirmPassword) { setError("The passwords do not match."); return; }
    if (password.length < 6) { setError("Passwords need at least 6 characters."); return; }

    setIsLoading(true);
    try {
      const result = isSignUp ? await signUp(email, password, name.trim()) : await signIn(email, password);
      if (result.error) { setError(result.error); return; }
      if (result.user) onLogin(result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in did not work. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogle = async () => {
    setError(null);
    const { error: err } = await signInWithGoogle();
    if (err) setError(err);
  };

  return (
    <div className="grid h-full w-full overflow-y-auto bg-background lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]" data-section="core">
      {/* Product side (desktop) */}
      <aside className="band hidden flex-col justify-between p-10 lg:flex xl:p-14">
        <div className="flex items-center gap-3">
          <span className="font-display text-2xl text-white">SPACEAI <span className="text-green-fill">FC</span></span>
        </div>
        <div className="max-w-xl">
          <h1 className="text-6xl text-text-primary xl:text-7xl">Read the game from where the players stand.</h1>
          <p className="mt-4 text-lg text-text-secondary">
            Formations, pass networks, space control, pressing and tactical patterns, turned into prioritised
            recommendations and a written briefing.
          </p>
          <div className="mt-8">
            <PitchPreview teamA={teamA} teamB={teamB} teamAColor={DEMO_TEAM_A_COLOR} teamBColor={DEMO_TEAM_B_COLOR} passes={DEMO_PASSES} showNames={false} passDelay={0.4} />
          </div>
        </div>
        <p className="text-sm text-text-muted">Built by Yassin Youssef</p>
      </aside>

      {/* Form side */}
      <div className="flex items-center justify-center px-4 py-10 sm:px-8">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: EASE_OUT }} className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="font-display text-2xl text-text-primary">SPACEAI <span className="text-green">FC</span></span>
          </div>

          <h2 className="text-4xl uppercase text-text-primary">{isSignUp ? "Create an account" : "Sign in"}</h2>
          <p className="mt-1 text-sm text-text-secondary">
            {configured ? "An account keeps a history of your analyses. Everything else works as a guest." : "Every feature works as a guest."}
          </p>

          {!configured && (
            <div className="mt-5 flex items-start gap-2 rounded-md border border-warning/50 bg-warning/5 p-3 text-sm text-text-secondary">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
              <span>Accounts are switched off on this install because Supabase is not configured, so saved history is unavailable.</span>
            </div>
          )}

          <Button variant={configured ? "secondary" : "primary"} size="lg" block icon={UserRound} onClick={onGuest} className="mt-6">
            Continue as guest
          </Button>

          {configured && (
            <>
              <div className="my-6 flex items-center gap-3 text-sm text-text-muted">
                <span className="h-px flex-1 bg-line" /> or with email <span className="h-px flex-1 bg-line" />
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <AnimatePresence initial={false}>
                  {isSignUp && (
                    <motion.div key="name" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2, ease: EASE_OUT }} className="overflow-hidden">
                      <Field icon={User} label="Name" type="text" value={name} onChange={setName} placeholder="Your name" autoComplete="name" required />
                    </motion.div>
                  )}
                </AnimatePresence>
                <Field icon={Mail} label="Email" type="email" value={email} onChange={setEmail} placeholder="you@club.com" autoComplete="email" required />
                <Field icon={Lock} label="Password" type="password" value={password} onChange={setPassword} placeholder="At least 6 characters" autoComplete={isSignUp ? "new-password" : "current-password"} required />
                <AnimatePresence initial={false}>
                  {isSignUp && (
                    <motion.div key="confirm" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2, ease: EASE_OUT }} className="overflow-hidden">
                      <Field icon={Lock} label="Confirm password" type="password" value={confirmPassword} onChange={setConfirmPassword} placeholder="Repeat the password" autoComplete="new-password" required />
                    </motion.div>
                  )}
                </AnimatePresence>

                {error && (
                  <p role="alert" className="rounded-md border border-danger/50 bg-danger/10 px-3 py-2.5 text-sm text-danger">{error}</p>
                )}

                <Button type="submit" size="lg" block loading={isLoading}>
                  {isLoading ? (isSignUp ? "Creating account…" : "Signing in…") : isSignUp ? "Create account" : "Sign in"}
                </Button>
              </form>

              <button type="button" onClick={handleGoogle} className="press mt-3 flex h-12 w-full items-center justify-center gap-3 rounded-md border border-line-strong bg-surface-1 font-medium text-text-primary hover:bg-surface-2">
                <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden>
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                Continue with Google
              </button>

              <p className="mt-6 text-sm text-text-secondary">
                {isSignUp ? "Already have an account? " : "New here? "}
                <button type="button" onClick={() => { setIsSignUp(!isSignUp); setError(null); }} className="font-medium text-section underline-offset-4 hover:underline">
                  {isSignUp ? "Sign in" : "Create an account"}
                </button>
              </p>
            </>
          )}
        </motion.div>
      </div>
    </div>
  );
}

function Field({ icon: Icon, label, type, value, onChange, placeholder, autoComplete, required }: { icon: typeof Mail; label: string; type: string; value: string; onChange: (v: string) => void; placeholder: string; autoComplete?: string; required?: boolean }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      <span className="relative block">
        <Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} autoComplete={autoComplete} required={required} className="field h-11 pl-9 text-base" />
      </span>
    </label>
  );
}
