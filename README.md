# GEMI Open Data Python client

A small Python client for the official Open Data API of Greece's General
Commercial Registry (Γενικό Εμπορικό Μητρώο, GEMI).

> Early scaffold: the API client exposes the documented endpoints and returns
> the API's JSON payloads directly. Typed response models and a CLI may be
> added in later releases.

## Install from source

```shell
git clone https://github.com/takispanag/gemi-opendata-python.git
cd gemi-opendata-python
python -m pip install -e .
```

This project has not been published to PyPI yet.

## Usage

Request an API key from the [official GEMI Open Data portal](https://opendata.businessportal.gr/).
The Swagger page's `api-docs-key` is for limited documentation testing; it does
not replace requesting your own key.

```python
import os

from gemi_opendata import GemiClient

client = GemiClient(api_key=os.environ["GEMI_OPENDATA_API_KEY"])

matches = client.search_companies(afm="YOUR_AFM_HERE", resultsSize=10)
company = client.get_company(123456789000)
documents = client.get_company_documents(123456789000)

client.close()
```

At least one search criterion is required. Multiple criteria are combined with
AND by the API. Sequence values (for example, multiple KAD codes) are sent as
comma-separated values, as required by the API reference.

## API coverage

- Search companies and retrieve a company by GEMI number
- Retrieve a company's public documents and download document files
- Retrieve GEMI reference data: activities, prefectures, municipalities,
  company statuses, legal types, GEMI offices, and assembly subjects
- Check API health

## Documentation and data terms

- [Official technical documentation](https://opendata.businessportal.gr/techdocs/)
- [Official Swagger / OpenAPI 2.0 specification](https://opendata-api.businessportal.gr/api-docs)
- The API's published data license is ODC-BY-1.0. Data consumers must follow
  its attribution terms. This client is independently licensed under MIT.

The project is not affiliated with or endorsed by GEMI, KEEE, or the Greek
Ministry of Development. Do not commit API keys; use an environment variable or
a secret manager.

