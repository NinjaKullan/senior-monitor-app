# Serve the prebuilt dist/ with nginx — same server and same caching contract
# as the webapp (DECISIONS 112, ported by test_site_caching.py). The build
# still happens outside the image: `npm run ci` produces and verifies dist/,
# and the founder deploys what was checked, not a second build of it.
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html
# DECISIONS 191: file permissions must not be able to break serving. An asset
# written by a bridge arrived mode 0600, survived vite's copy into dist/ and
# Docker's COPY unchanged, and nginx's non-root worker answered 403 for that one
# file — a broken image on a live page, from a mode bit nobody set on purpose.
# `a+rX` is read for everyone on files and traverse on directories, which is
# what a static document root wants in every case.
RUN chmod -R a+rX /usr/share/nginx/html
# The config-level half of DECISIONS 168: a conf that does not parse cannot
# become an image, so `fly deploy` fails at build instead of at serve. The
# behavioral half (host dispatch, the 148 loop) lives in the site suite.
RUN nginx -t
EXPOSE 8080
