# devops-capstone-project

[![CI Build](https://github.com/Nura007/devops-capstone-project/actions/workflows/ci-build.yaml/badge.svg?branch=main)](https://github.com/Nura007/devops-capstone-project/actions/workflows/ci-build.yaml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Customer Accounts is a RESTful microservice for managing customer information for an e-commerce website. This IBM DevOps Capstone project covers agile planning, test-driven development, automated continuous integration, HTTP security, Docker containers, Kubernetes deployment, and a Tekton continuous delivery pipeline.

## Service API

| Method | Endpoint | Purpose | Successful response |
| --- | --- | --- | --- |
| GET | `/` | Service information | 200 with JSON |
| GET | `/health` | Health check | 200 with JSON |
| POST | `/accounts` | Create an account | 201 with account and Location header |
| GET | `/accounts` | List accounts | 200 with JSON array |
| GET | `/accounts/{id}` | Read an account | 200 with account |
| PUT | `/accounts/{id}` | Update an account | 200 with updated account |
| DELETE | `/accounts/{id}` | Delete an account | 204 with no body |

Accounts contain `id`, `name`, `email`, `address`, `phone_number`, and `date_joined`. The server assigns the identifier. Requests and responses use JSON; dates use `YYYY-MM-DD`. The service reports missing accounts, invalid data, and unsupported content types with HTTP error responses.

## Development

Use Python 3.9 for compatibility with the course's `nosetests` toolchain. In the IBM Skills Network lab, initialize the supplied environment with:

```bash
source bin/setup.sh
```

For a local development environment:

```bash
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade 'pip<26' 'setuptools<81' wheel
python -m pip install -r requirements.txt
```

Start PostgreSQL, configure the database connection, and start the service:

```bash
docker run -d --name accounts-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=accounts postgres:15-alpine
export DATABASE_URI=postgresql://postgres:postgres@localhost:5432/accounts
flask run --host=0.0.0.0 --port=8080
```

The credentials above are disposable local development values. Configure `DATABASE_URI` and `SECRET_KEY` through environment variables for your deployment, and keep secrets out of source control.

## Testing and continuous integration

```bash
flake8 service tests --count --statistics
nosetests
coverage report -m
```

`setup.cfg` enables verbose tests, a fresh coverage run, missing-line reporting, and a minimum of 95% coverage of `service`. It also contains Flake8 and Pylint configuration. Tests cover the database model, REST API, error handling, security headers, and CORS behavior.

The [CI Build workflow](.github/workflows/ci-build.yaml) runs on pushes and pull requests to `main`, or on manual dispatch. It checks out the code, prepares Python and PostgreSQL, installs dependencies, lints the code, runs `nosetests`, enforces the coverage threshold, and saves a coverage report. The badge above reflects the actual GitHub Actions result.

## Security

Flask-Talisman adds HTTP security headers, and Flask-CORS manages cross-origin requests. Security behavior is initialized in [`service/__init__.py`](service/__init__.py) and checked by the automated tests. HTTP is available for the course's local container and port-forwarding exercises; terminate TLS and configure trusted origins when deploying beyond the lab.

## Containers and delivery

The `Dockerfile` packages the service for port 8080. Kubernetes resources are stored under `deploy/`, and Tekton pipeline resources are under `tekton/`.

```bash
docker build -t accounts:1 .
docker run --rm -p 8080:8080 -e DATABASE_URI="$DATABASE_URI" accounts:1
```

When the database is outside the container, `DATABASE_URI` must use a hostname reachable from that container. Use the Kubernetes service name for cluster deployments.

## Planning

Work is organized into three one-week sprints: REST API development; continuous integration and security; containerization, Kubernetes, and continuous delivery. The reusable [user story template](.github/ISSUE_TEMPLATE/user-story.md) records the role, capability, benefit, assumptions, and Gherkin acceptance criteria.

## Attribution and license

Based on the [IBM Developer Skills Network DevOps Capstone template](https://github.com/ibm-developer-skills-network/aolwx-devops-capstone-template), created by John J. Rofrano and contributors. The starter model and framework retain their original attribution. Licensed under [Apache License 2.0](LICENSE).
