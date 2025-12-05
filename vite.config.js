import { join, dirname, resolve } from "path";
import { fileURLToPath } from "url";
import react from "@vitejs/plugin-react";
import mkcert from 'vite-plugin-mkcert'
import { defineConfig } from "vite";

const path = fileURLToPath(import.meta.url);

export default defineConfig({
  root: join(dirname(path), "client"),
  plugins: [
      react(),
      mkcert()
  ],
  server: {
    https: true,
    port: 3000
  },
  define: {
    'process.env': {}
  }
});
