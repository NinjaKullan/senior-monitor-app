FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# The package imports as `care`, so it sits one level down. Tests, scripts and
# the fixtures stay out (.dockerignore).
COPY . ./care

# The checked-in centroids may still be the 200-row sample (DECISIONS 344).
# An image built from it would answer ZIP_UNKNOWN for most of the country, so
# it is refused here: run scripts/make_zcta.py first, which deletes the marker.
RUN test ! -f care/data/zcta.SAMPLE \
    || (echo "care/data/zcta.csv is the sample; run care/scripts/make_zcta.py" && exit 1)

EXPOSE 8080

# No access log (§6): a request line is not ours to keep.
CMD ["uvicorn", "care.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
