FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
RUN npm ci

COPY apps/web ./apps/web

ARG NEXT_PUBLIC_XFOLLOW_API_BASE_URL=http://localhost:8101
ENV NEXT_PUBLIC_XFOLLOW_API_BASE_URL=${NEXT_PUBLIC_XFOLLOW_API_BASE_URL}

RUN npm run build --workspace apps/web

FROM node:22-alpine AS runtime

WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /app/package.json /app/package-lock.json ./
COPY --from=build /app/apps/web/package.json ./apps/web/package.json
COPY --from=build /app/apps/web/.next ./apps/web/.next
COPY --from=build /app/apps/web/public ./apps/web/public
COPY --from=build /app/apps/web/next.config.mjs ./apps/web/next.config.mjs

RUN npm ci --omit=dev

EXPOSE 3000

CMD ["npm", "--workspace", "apps/web", "run", "start"]
