import { useState } from 'react';
import { Send } from 'lucide-react';

export default function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await onLogin(username, password);
    } catch (loginError) {
      setError(loginError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#181816] px-4 text-[#edece6]">
      <section className="w-full max-w-sm rounded-2xl border border-[#383834] bg-[#242422] p-7 shadow-2xl">
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#d97757] text-white">
            <Send size={18} aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">CodePilot</h1>
            <p className="text-sm text-[#9c9a92]">Sign in to continue</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block space-y-1.5 text-sm text-[#c5c3bb]">
            <span>Username</span>
            <input
              autoComplete="username"
              autoFocus
              required
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className="w-full rounded-lg border border-[#44443f] bg-[#181816] px-3 py-2.5 text-[#edece6] outline-none focus:border-[#d97757]"
            />
          </label>

          <label className="block space-y-1.5 text-sm text-[#c5c3bb]">
            <span>Password</span>
            <input
              autoComplete="current-password"
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-lg border border-[#44443f] bg-[#181816] px-3 py-2.5 text-[#edece6] outline-none focus:border-[#d97757]"
            />
          </label>

          {error && (
            <p role="alert" className="text-sm text-rose-300">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !username || !password}
            className="w-full rounded-lg bg-[#d97757] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#e28567] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  );
}
