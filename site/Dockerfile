# Serve the prebuilt dist/ with nginx — same server and same caching contract
# as the webapp (QUESTIONS 112, ported by test_site_caching.py). The build
# still happens outside the image: `npm run ci` produces and verifies dist/,
# and the founder deploys what was checked, not a second build of it.
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html
EXPOSE 8080
