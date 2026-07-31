/// <reference types="vite/client" />

/**
 * The only two values this app is allowed to read from the environment.
 * Both are safe to ship in a public bundle; anything else belongs on a server.
 */
interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string;
  readonly VITE_SUPABASE_PUBLISHABLE_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
