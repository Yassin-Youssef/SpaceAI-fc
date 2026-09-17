import { motion, AnimatePresence } from "motion/react";
import { Mail, Lock, User, ArrowRight, Loader2, UserRound, AlertTriangle } from "lucide-react";
import { useState } from "react";
import { signIn, signUp, signInWithGoogle, isSupabaseConfigured } from "../../lib/supabase";
import type { UserProfile } from "../../lib/types";
import { pressable } from "../../lib/motion";

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (isSignUp && name.trim().length < 2) { setError("Please enter your name."); return; }
    if (isSignUp && password !== confirmPassword) { setError("Passwords do not match."); return; }
    if (password.length < 6) { setError("Password must be at least 6 characters."); return; }

    setIsLoading(true);
    try {
      const result = isSignUp ? await signUp(email, password, name.trim()) : await signIn(email, password);
      if (result.error) { setError(result.error); return; }
      if (result.user) onLogin(result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
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
    <div className="relative flex h-full w-full items-center justify-center overflow-y-auto bg-background p-4">
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at top, rgba(0,217,255,0.16) 0%, transparent 55%), radial-gradient(ellipse at bottom right, rgba(123,97,255,0.14) 0%, transparent 50%)" }} />
        <div className="pitch-grid-bg absolute inset-0 opacity-50" />
      </div>

      <motion.div initial={{ opacity: 0, scale: 0.94, y: 16 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }} className="relative z-10 w-full max-w-md">
        <div className="rounded-2xl border border-brand/20 p-6 backdrop-blur-2xl sm:p-8" style={{ background: "linear-gradient(135deg, rgba(18,24,53,0.85) 0%, rgba(10,14,39,0.85) 100%)", boxShadow: "0 0 60px rgba(0,217,255,0.18)" }}>
          {/* Logo */}
          <div className="mb-6 flex justify-center">
            <motion.div
              className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500 via-blue-600 to-violet-600"
              animate={{ boxShadow: ["0 0 30px rgba(0,217,255,0.35)", "0 0 55px rgba(0,217,255,0.6)", "0 0 30px rgba(0,217,255,0.35)"] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
            >
              <svg viewBox="0 0 64 64" className="h-9 w-9" aria-hidden><circle cx="32" cy="32" r="22" fill="none" stroke="#fff" strokeWidth="4" /><path d="M32 14l8 6-3 10H27l-3-10z" fill="#fff" /><circle cx="32" cy="32" r="4" fill="#fff" /></svg>
            </motion.div>
          </div>

          <div className="mb-6 text-center">
            <h1 className="text-2xl font-bold text-white sm:text-3xl">
              {isSignUp ? "Join " : "Welcome to "}<span className="text-brand">SpaceAI FC</span>
            </h1>
            <p className="mt-1 text-sm text-text-secondary">Agentic tactical intelligence for football</p>
          </div>

          {!configured && (
            <div className="mb-5 flex items-start gap-2 rounded-xl border border-warning/30 bg-warning/10 p-3 text-xs text-warning">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>Supabase isn't configured, so accounts and saved history are disabled. You can still use every feature as a guest.</span>
            </div>
          )}

          {/* Guest first-class when auth is unavailable */}
          <motion.button {...pressable} type="button" onClick={onGuest} className={`mb-5 flex w-full items-center justify-center gap-2 rounded-xl py-3 font-bold transition-shadow ${configured ? "border border-white/10 bg-white/5 text-white hover:bg-white/10" : "bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:shadow-[0_0_40px_rgba(0,217,255,0.4)]"}`}>
            <UserRound className="h-5 w-5" /> Continue as guest
          </motion.button>

          {configured && (
            <>
              <div className="my-5 flex items-center gap-4">
                <div className="h-px flex-1 bg-white/10" /><span className="text-xs uppercase tracking-widest text-text-muted">or sign in</span><div className="h-px flex-1 bg-white/10" />
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <AnimatePresence initial={false}>
                  {isSignUp && (
                    <motion.div key="name" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                      <Field icon={User} label="Full name" type="text" value={name} onChange={setName} placeholder="Your name" autoComplete="name" required />
                    </motion.div>
                  )}
                </AnimatePresence>
                <Field icon={Mail} label="Email" type="email" value={email} onChange={setEmail} placeholder="you@example.com" autoComplete="email" required />
                <Field icon={Lock} label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" autoComplete={isSignUp ? "new-password" : "current-password"} required />
                <AnimatePresence initial={false}>
                  {isSignUp && (
                    <motion.div key="confirm" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                      <Field icon={Lock} label="Confirm password" type="password" value={confirmPassword} onChange={setConfirmPassword} placeholder="••••••••" autoComplete="new-password" required />
                    </motion.div>
                  )}
                </AnimatePresence>

                <AnimatePresence>
                  {error && (
                    <motion.div key="err" initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
                      {error}
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.button {...(isLoading ? {} : pressable)} type="submit" disabled={isLoading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 py-3 font-bold text-white transition-shadow hover:shadow-[0_0_40px_rgba(0,217,255,0.4)] disabled:cursor-not-allowed disabled:opacity-70">
                  {isLoading ? <><Loader2 className="h-5 w-5 animate-spin" /> {isSignUp ? "Creating account…" : "Signing in…"}</> : <>{isSignUp ? "Create account" : "Sign in"} <ArrowRight className="h-5 w-5" /></>}
                </motion.button>
              </form>

              <button type="button" onClick={handleGoogle} className="mt-3 flex w-full items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/5 py-3 font-medium text-white transition-colors hover:bg-white/10">
                <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden>
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                Continue with Google
              </button>

              <div className="mt-5 text-center">
                <button type="button" onClick={() => { setIsSignUp(!isSignUp); setError(null); }} className="text-sm text-text-secondary transition-colors hover:text-brand">
                  {isSignUp ? <>Already have an account? <span className="font-semibold">Sign in</span></> : <>Don't have an account? <span className="font-semibold">Sign up</span></>}
                </button>
              </div>
            </>
          )}
        </div>
        <p className="mt-4 text-center text-xs text-text-muted">Built by Yassin Youssef · Sense → Understand → Reason → Act → Explain</p>
      </motion.div>
    </div>
  );
}

function Field({ icon: Icon, label, type, value, onChange, placeholder, autoComplete, required }: { icon: typeof Mail; label: string; type: string; value: string; onChange: (v: string) => void; placeholder: string; autoComplete?: string; required?: boolean }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-text-secondary">{label}</span>
      <span className="relative block">
        <Icon className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} autoComplete={autoComplete} required={required} className="field rounded-xl py-3 pl-11 pr-4 text-base" />
      </span>
    </label>
  );
}
