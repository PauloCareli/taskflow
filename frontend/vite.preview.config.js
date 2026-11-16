// Configuration for the web container (see `Dockerfile`): serve the built files and forward
// `/api` to the API. Kept apart from `vite.config.ts` so the image needs none of the build tooling.
const upstream = process.env.API_UPSTREAM ?? 'http://api:8000'

export default {
  preview: {
    host: '0.0.0.0',
    port: 8080,
    strictPort: true,
    proxy: {
      '/api': {
        target: upstream,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
}
