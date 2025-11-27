FROM node:20-alpine
WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY tsconfig.json ./
COPY index.ts local-server.ts ./

RUN npm run build

ENV PORT=8080
EXPOSE 8080
CMD ["node", "dist/local-server.js"]