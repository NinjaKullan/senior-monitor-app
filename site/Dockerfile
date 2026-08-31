# Serve the prebuilt dist/ with nginx — same server and same caching contract
# as the webapp (DECISIONS 112, ported by test_site_caching.py). The build
# still happens outside the image: `npm run ci` produces and verifies dist/,
# and the founder deploys what was checked, not a second build of it.
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html
# DECISIONS 191: file permissions must not be able to break serving. An asset
# written by a tool rather than by git arrived mode 0600, survived vite's copy
# into dist/ and Docker's COPY unchanged, and nginx's non-root worker answered
# 403 for that one file — a broken image on a live page, from a mode bit nobody
# set on purpose. `a+rX` is read for everyone on files and traverse on
# directories, which is what a static document root wants in every case, and it
# runs AFTER the copy because before it the directory is empty.
RUN chmod -R a+rX /usr/share/nginx/html
# The config-level half of DECISIONS 168: a conf that does not parse cannot
# become an image, so `fly deploy` fails at build instead of at serve. The
# behavioral half (host dispatch, the 148 loop) lives in the site suite.
RUN nginx -t

# The counter sidecar (DECISIONS 201/211/212, docs/log-summary-job-design.md
# option C). One interpreter and one file, no new app and no new storage: it
# runs nginx as its child, reads the three-field access log off its stdout,
# tallies allowlisted paths in memory, and POSTs counts to kettle-api. python3
# is the one dependency added to this image, and it earns it by being the
# whole runtime — stdlib urllib for the POST, stdlib ElementTree for the
# sitemap-derived allowlist, no pip install and no requirements file. The
# alternative (busybox awk plus curl) is smaller and is not testable from the
# suite that has to prove the allowlist excludes what is not on it.
RUN apk add --no-cache python3
COPY counter/kettle_counter.py /usr/local/bin/kettle_counter.py

EXPOSE 8080
# nginx is no longer PID 1: the counter is, and nginx is its child. That is
# what lets one process read the other's log stream with no file, no FIFO and
# no volume. The counter forwards SIGTERM, exits with nginx's own code, and
# treats draining that stdout as its only guaranteed duty — with the metrics
# secret unset it is a pass-through pipe and the image serves exactly as it
# did before.
CMD ["python3", "/usr/local/bin/kettle_counter.py"]
