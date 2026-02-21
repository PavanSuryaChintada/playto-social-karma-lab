FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install
COPY . .

EXPOSE 5173

ENV VITE_API_URL=https://playto-social-karma-lab.onrender.com/api

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
