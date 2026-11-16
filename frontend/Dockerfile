FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# The browser calls `/api`; the web container forwards it to the API when it starts.
ENV VITE_API_BASE_URL=/api
RUN npm run build

FROM node:22-alpine
ENV NODE_ENV=production
WORKDIR /srv
# Serving the build only needs Vite itself, at the version the lockfile pins.
COPY --from=build /app/package-lock.json /tmp/package-lock.json
RUN VITE_VERSION="$(node -p "require('/tmp/package-lock.json').packages['node_modules/vite'].version")" \
    && npm init -y > /dev/null \
    && npm pkg set type=module > /dev/null \
    && npm install --no-audit --no-fund "vite@${VITE_VERSION}" \
    && rm /tmp/package-lock.json
COPY --from=build /app/dist ./dist
COPY vite.preview.config.js ./
USER node
EXPOSE 8080
# `--configLoader native` imports the plain ESM config directly. The default loader writes a
# temporary file next to it, which the non-root user is not allowed to do.
CMD ["node", "node_modules/vite/bin/vite.js", "preview", "--config", "vite.preview.config.js", "--configLoader", "native"]
