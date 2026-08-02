/// <reference types="vite/client" />

/**
 * The only value this page reads from the environment, and it is a public URL.
 * There is nothing else: no key, no token, no analytics id — this site has no
 * credential to leak because it holds none.
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
