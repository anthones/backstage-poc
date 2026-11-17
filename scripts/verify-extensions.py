"""Verify customer-facing outcomes and Jira provenance in the running local PoC."""
import argparse
import json
import urllib.error
import urllib.request


def call(port, path, body=None):
    request = urllib.request.Request(f'http://localhost:{port}{path}', data=json.dumps(body).encode() if body is not None else None,
                                     headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(request, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def fault(enabled):
    assert call(8083, '/demo/fault', {'enabled': enabled})[0] == 200


def main(live=False):
    fault(False)
    status, data = call(8080, '/api/activation', {'tenant_id': 'tenant-acme'})
    assert status == 200 and data['result']['activation'] == 'ready'
    assert data['simulation'] is True
    fault(True)
    assert call(8080, '/api/subscription?tenant=tenant-acme')[0] == 200
    status, data = call(8080, '/api/activation', {'tenant_id': 'tenant-acme'})
    assert status == 502 and data['root_cause'] == {'service': 'policy-service', 'owner': 'cloud-security', 'code': 'policy_unavailable'}
    assert data['request_id']
    fault(False)
    assert call(8080, '/api/activation', {'tenant_id': 'tenant-acme'})[0] == 200
    status, data = call(8080, '/api/activation', {'tenant_id': 'tenant-suspended'})
    assert status == 502 and data['root_cause']['owner'] == 'commerce'
    status, data = call(8090, '/issues?source=scenario&component=customer-portal')
    assert status == 200 and data['source'] == 'scenario'
    assert {i['key'] for i in data['issues']} == {'ACT-104', 'ACT-106'}
    assert all(i['url'] is None for i in data['issues'])
    print('PASS: customer API success, outage with subscription still available, recovery, blocked subscription, and catalog-mapped fictional work.')
    if live:
        status, data = call(8090, '/issues?source=public')
        assert status == 200, data
        assert data['source'] == 'public' and data['component'] is None
        assert data['issues'] and all(i['url'].startswith('https://jira.atlassian.com/browse/') for i in data['issues'])
        print(f"PASS: live read-only Atlassian Jira API returned {len(data['issues'])} public issues, labelled separately from fictional work.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-jira', action='store_true', help='Also request live public Jira data through the adapter')
    args = parser.parse_args()
    try:
        main(args.public_jira)
    finally:
        fault(False)
