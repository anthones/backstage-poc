"""Behavior checks for browser/API boundaries and Jira provenance; no external network."""
import asyncio
import importlib.util
import json
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


portal = module('portal', 'frontend/customer-portal/main.py')
jira = module('jira', 'integrations/jira/main.py')


def run(app, method, path, **kwargs):
    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(request())


@pytest.mark.parametrize('action,path,method,backend_path,status,owner', [
    ('activation', '/api/activation', 'POST', '/v1/activations', 502, 'cloud-security'),
    ('subscription', '/api/subscription?tenant=tenant-acme', 'GET', '/v1/subscriptions/tenant-acme', 409, 'commerce'),
])
def test_portal_preserves_failure_and_request_correlation(action, path, method, backend_path, status, owner):
    def upstream(request):
        assert request.method == method
        assert request.url.path == backend_path
        request_id = request.headers['X-Request-ID']
        if action == 'activation':
            assert json.loads(request.content) == {'tenant_id': 'tenant-acme'}
        return httpx.Response(status, json={'request_id': request_id, 'root_cause': {'owner': owner}})
    app = portal.create_app(httpx.MockTransport(upstream))
    response = run(app, method, path, **({'json': {'tenant_id': 'tenant-acme'}} if method == 'POST' else {}))
    assert response.status_code == status
    assert response.json()['root_cause']['owner'] == owner
    assert response.headers['X-Request-ID'] == response.json()['request_id']


def test_portal_forwards_success_and_reports_upstream_timeout():
    response = run(portal.create_app(httpx.MockTransport(lambda req: httpx.Response(200, json={'result': {'activation': 'ready'}, 'simulation': True}))), 'POST', '/api/activation', json={'tenant_id': 'tenant-acme'})
    assert response.status_code == 200 and response.json()['simulation'] is True
    def timeout(request):
        raise httpx.ReadTimeout('demo timeout')
    response = run(portal.create_app(httpx.MockTransport(timeout)), 'POST', '/api/activation', json={'tenant_id': 'tenant-acme'})
    assert response.status_code == 502
    assert response.json()['root_cause'] == {'service': 'onboarding-service', 'owner': 'customer-experience', 'code': 'unreachable_or_timeout'}


def test_invalid_customer_never_reaches_a_backend():
    def unexpected(request):
        pytest.fail('Invalid customer was forwarded')
    app = portal.create_app(httpx.MockTransport(unexpected))
    assert run(app, 'POST', '/api/activation', json={'tenant_id': '../secret'}).status_code == 422
    assert run(app, 'GET', '/api/subscription?tenant=../secret').status_code == 422


def test_live_jira_is_a_real_search_and_preserves_link_direction():
    def upstream(request):
        assert str(request.url).startswith('https://jira.atlassian.com/rest/api/2/search?')
        assert request.url.params['jql'] == 'project = JRASERVER ORDER BY updated DESC'
        assert request.url.params['maxResults'] == '5'
        assert 'Authorization' not in request.headers
        return httpx.Response(200, json={'total': 2, 'issues': [{'key': 'JRASERVER-1', 'fields': {'summary': 'Public example', 'status': {'name': 'Open'}, 'issuelinks': [{'type': {'inward': 'is blocked by'}, 'inwardIssue': {'key': 'JRASERVER-2'}}]}}]})
    response = run(jira.create_app(httpx.MockTransport(upstream)), 'GET', '/issues?source=public')
    data = response.json()
    assert data['source'] == 'public' and data['has_more']
    assert data['component'] is None
    assert data['issues'][0]['url'] == 'https://jira.atlassian.com/browse/JRASERVER-1'
    assert data['issues'][0]['links'] == [{'key': 'JRASERVER-2', 'relationship': 'is blocked by'}]
    assert 'unrelated' in data['notice']


def test_live_jira_failure_never_becomes_fictional_success():
    app = jira.create_app(httpx.MockTransport(lambda req: httpx.Response(429)))
    response = run(app, 'GET', '/issues?source=public')
    assert response.status_code == 503
    assert 'issues' not in response.json()
    assert run(app, 'GET', '/issues?source=public&component=customer-portal').status_code == 400


def test_scenario_uses_catalog_mapping_and_exposes_no_fake_jira_links():
    response = run(jira.create_app(), 'GET', '/issues?source=scenario&component=customer-portal')
    data = response.json()
    assert data['source'] == 'scenario'
    assert data['component']['owner'] == 'customer-experience'
    assert {i['key'] for i in data['issues']} == {'ACT-104', 'ACT-106'}
    assert all(i['url'] is None for i in data['issues'])
    assert 'labels = "customer-portal"' in data['jql']
    assert run(jira.create_app(), 'GET', '/issues?source=scenario&component=unknown').status_code == 404
