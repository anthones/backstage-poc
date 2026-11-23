# KiwiTCMS: Official references

[Overview](README.md) · [RFC-002](RFC-002-kiwitcms-adoption.md)

**Sources reviewed: 2026-11-19. No production release, image or identity integration is selected.**

Verify these findings against the selected production release. Online documentation and development code change.

## Production and image selection

Upstream requires production containers. The Community example uses MariaDB and separate database/upload volumes.
Use settings overrides or a maintained downstream image. Do not deploy a floating development branch.
[Production guide](https://kiwitcms.readthedocs.io/en/latest/installing_docker.html)

The public image is rolling; subscribers can obtain tagged images. Preserve an approved digest or reproducible source build.
Compare component licenses, paid features and support costs.
[Images](https://kiwitcms.org/containers/), [edition matrix](https://kiwitcms.org/features/)

## Tracking, ads and translation resources

`ANONYMOUS_ANALYTICS=False` disables supported usage analytics. Development and production defaults differ.
[Analytics guidance](https://kiwitcms.org/blog/kiwi-tcms-team/2024/02/23/anonymous-analytics-via-plausibleio/)

The base template gates Plausible/Scarf requests on that setting. Crowdin translation resources use a separate locale condition.
Advertising uses a separate EthicalAds include. Hiding ads does not stop requests.
Verify browser/server traffic in production mode across supported locales.
[Base template](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/templates/base.html), [ads](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/templates/include/ads.html), [overrides](https://kiwitcms.org/blog/tags/customization/)

The internal “Telemetry” area contains test reports and dashboards. Retain these reports while disabling external tracking.
[Reporting navigation](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/settings/common.py)

## Configuration and access documentation

Use the selected release's settings for registration, account activation and identity integration.
[Settings](https://kiwitcms.readthedocs.io/en/latest/configuration.html), [registration](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/kiwi_auth/views.py), [identity options](https://kiwitcms.org/blog/kiwi-tcms-team/2025/08/28/enterprise-subscription-explained/)

The upstream administration guide covers groups, permissions and their API limits.
[Administration guide](https://kiwitcms.readthedocs.io/en/latest/admin.html)

## History, recovery and connectors

Execution records store a case-text history version. Verify old results remain understandable after edits and migration.
[Case history](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/testcases/models.py), [executions](https://raw.githubusercontent.com/kiwitcms/Kiwi/master/tcms/testruns/models.py)

Back up and restore database records and attachments together. A database restore alone does not recover uploaded files.
[Backup guidance](https://kiwitcms.org/blog/atodorov/2018/07/30/how-to-backup-docker-volumes-for-kiwi-tcms/)

Use the selected release’s production configuration guidance.
[Production settings](https://kiwitcms.readthedocs.io/en/latest/configuration.html)
