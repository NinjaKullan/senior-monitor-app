# Serve the prebuilt dist/ with nginx — same server and same caching contract
# as the webapp (DECISIONS 112, ported by test_site_caching.py). The build
# still happens outside the image: `npm run ci` produces and verifies dist/,
# and the founder deploys what was checked, not a second build of it.
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html
# Normalize read permissions: a file that reached the repo with owner-only
# perms (e.g. written by a tool, not git) would otherwise 403 from nginx.
RUN chmod -R a+rX /usr/share/nginx/html
# The config-level half of DECISIONS 168: a conf that does not parse cannot
# become an image, so `fly deploy` fails at build instead of at serve. The
# behavioral half (host dispatch, the 148 loop) lives in the site suite.
RUN nginx -t
EXPOSE 8080
