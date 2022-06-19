FROM node:lts-alpine

# copy both 'package.json' and 'package-lock.json' (if available)
COPY package*.json ./

# install project dependencies
RUN npm install

# copy project files and folders to the current working directory (i.e. 'app' folder)
COPY . .

# set your env before the build process
ENV VUE_APP_BASE_URL=https://portal.ris.beuth-hochschule.de

EXPOSE 8086

CMD [ "npm", "run", "serve"]


