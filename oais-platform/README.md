# OAIS platform

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)

This is the backend implementation of the OAIS Platform of the CERN Digital Memory, built on Django.

It provides a REST API which can be used to interact with the platform.

The main goals of the platform are:

- Allow users to trigger the _harvesting_ of resources and produce SIPs (using the [bagit-create](https://gitlab.cern.ch/digitalmemory/bagit-create) tool);
- Allow services and users to _deposit_ SIPs and ingest them in the platform;
- Trigger long-term preservation workflows and provide ways to manage them and check on their status;
  - Interface with a distributed deployment of Archivematica;
  - Send SIPs to Archiver.eu platforms and evaluate their interfaces, performance and behaviour on ingestions and processing metadata;
- Send prepared AIPs to the new CERN Tape Archive (CTA);
- Maintain a _registry_ of the successfully harvested and ingested resources, processing and exposing metadata;
- Expose resources on an access system

The platform is designed according to these principles:

- The implementation should reference the OAIS model;
- The products of the archival process (SIPs, AIPs, DIPs) must be able to live on their own;
- The platform target is to coordinate the long term preservation process and provide an orchestration between existing tools and proven frameworks, not to reimplement them or overlap with their responsibilities. The main external components the platform interacts with are:
  - [BagIt-Create](https://gitlab.cern.ch/digitalmemory/bagit-create), a tool able to harvest and pull data from supported upstream sources, creating SIPs compliant to our [specification](https://gitlab.cern.ch/digitalmemory/sip-spec);
  - [Archivematica](https://www.archivematica.org/), responsible of creating the AIPs, running the actual preservation services (re-encodings, file formats conversions, etc);
  - [InvenioRDM](https://inveniordm.web.cern.ch/), a digital repository framework providing an access system to the archived resources (and their artifacts).
  - [CERN Tape Archive (CTA)](https://cta.web.cern.ch/cta/), the final destination of the long term preservation packages.
- The platform must be fully usable through the exposed API surface, enabling any service to integrate a long term preservation strategy to their workflows.
  - A [web interface](https://gitlab.cern.ch/digitalmemory/oais-web) is also provided, allowing users to use the platform through any browser.

## Usage

A public instance of the platform is available over [https://dm-luteus.web.cern.ch/](https://dm-luteus.web.cern.ch/). Swagger API documentation can be found [here](https://dm-luteus.web.cern.ch/api/schema/swagger-ui/).

User documentation is available [here](docs/user.md).

## Run

Here's how you can run a local instance of the platform.

A docker-compose setup is provided in this repository, bringing up the following services:

| Container name | Software   | Role                            | Exposed endpoint               |
| :------------- | :--------- | ------------------------------- | ------------------------------ |
| oais_django    | Django     | Backend API                     | [:8000](http://localhost:8000) |
| oais_celery    | Celery     | Task queue and scheduler (Beat) |                                |
| oais_redis     | Redis      | Broker                          |                                |
| oais_psql      | Postgresql | Database                        |                                |
| oais_pgadmin   | PGAdmin    | Database Browser                | [:5050](http://localhost:5050) |
| oais_nginx     | Nginx      | Reverse Proxy                   | [:80](http://localhost:80)     |

To quickly setup a development instance, featuring hot-reloading on the backend:

```bash
# Start by cloning oais-platform
git clone ssh://git@gitlab.cern.ch:7999/digitalmemory/oais-platform.git
# Inside it, clone oais-web
git clone ssh://git@gitlab.cern.ch:7999/digitalmemory/oais-web.git oais-platform/oais-web
# Build the web application
cd oais-platform/oais-web
npm install --force
npm run build
# Go back to the oais-platform folder and launch the docker compose setup
cd ..
docker-compose up
```

Node version 14.19.3 or newer is required for for building the web application (use `node -v` to check the current version).

> If you also want the React application to hot-reload on file modifications, instead of running `npm run build`, keep a shell open and run `npm run serve`. Please note that by default this will open `localhost:3000`, but we actually want the React app served through nginx, so ignore that tab.

The following endpoints are then available, on `localhost`:

- `/` - Oais-web React application
- `/api` - Base OAIS Platform API endpoint
- `/api/schema` - OpenAPI 3 specification of the API
- `/api/schema/swagger-ui/` - Swagger UI documentation for the API

### Helper commands

A Makefile is included in the repository, providing some utility commands:

- `make admin` creates an admin user (with password `admin`) that can be immediately used to login
- `make reset-db` shuts of the database container, wipes it and brings it up again, resetting the instance to an empty state
- `make shell` will attach to a shell in the Django container

### Django

To run these commands inside a Docker container, run it in the container shell with `docker exec -it oais_django sh`.

```bash
# python manage.py showmigrations
# Prepare migrations
python manage.py makemigrations oais
# Apply migrations
python manage.py migrate
# Create administrator user
DJANGO_SUPERUSER_PASSWORD=root DJANGO_SUPERUSER_USERNAME=root DJANGO_SUPERUSER_EMAIL=root@root.com python3 manage.py createsuperuser --noinput
# Run the application
python manage.py runserver
```

See [troubleshooting](docs/troubleshooting.md) for further instructions on how to maintain an instance and debug issues.

### Run tests

```bash
python manage.py test
```

With docker-compose:

```bash
docker-compose down
docker volume prune -y
docker-compose -f test-compose.yml up --exit-code-from django
```

Code is formatted using **black** and linted with **flake8**. A VSCode settings file is provided for convenience.

## Configuration

### CERN SSO

To enable the CERN SSO login, set Client ID and Client Secret from your application on https://application-portal.web.cern.ch/. Documentation can be found at https://auth.docs.cern.ch/applications/sso-registration/.

When adding a new "CERN SSO Registration" select OIDC. The redirect URI should be pointing to the `/api/oidc/callback/` endpoint (e.g. `https://<NAME>.web.cern.ch/api/oidc/callback/`) and the Base URL should be something like `https://<NAME>.web.cern.ch`.

```bash
# Secrets for OpenID Connect
export OIDC_RP_CLIENT_ID="Put here the Client ID"
export OIDC_RP_CLIENT_SECRET="Put here the Client Secret"
```

### Sentry

To set up Sentry, set the endpoint with the `SENTRY_DSN` environment variable. To get this value go to your Sentry instance dashboard - Settings - (Select or create a project) - SDK Setup - DSN.

```bash
export SENTRY_DSN="Put here the Sentry SDK client key"
```

### InvenioRDM

To be able to connect the platform with InvenioRDM, create a new API Token in your InvenioRDM instance (Log in - My Account - Applications - Personal access tokens - New token).

```bash
export INVENIO_API_TOKEN=<YOUR_INVENIO_API_TOKEN_HERE>
export INVENIO_SERVER_URL=<YOUR_INVENIO_SERVER_URL_HERE>
```

## CI/CD

The CI configured on this repository to run the tests on every commit and trigger an upstream deployment.

The platform gets deployed with Helm Charts on a Kubernetes cluster from CERN OpenShift. To learn more, check the [openshift-deploy](https://gitlab.cern.ch/digitalmemory/openshift-deploy) repository.

Two deployments are currently online:

- dm-luteus, tracking stable branches of the backend and the frontend
- dm-galanos, tracking development branches of the backend and the frontend
