#!/usr/bin/env python3
"""OPTIONAL browser evidence: requires Playwright and installed Chrome, not core dependencies.

Run with .venv-label-studio/bin/python scripts/verify_local_browser.py
Add --label-studio to initialize an isolated local fictional reviewer and import tasks
into the northstar-quality-pilot container. No credentials are stored or printed.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8087'


def local_account():
    code = '''
import json
import secrets
from importlib.metadata import version
from users.models import User
from organizations.models import Organization
user, created = User.objects.get_or_create(email='reviewer@example.invalid', defaults={'username': 'portfolio-reviewer', 'allow_newsletters': False})
password = secrets.token_urlsafe(32)
user.set_password(password)
user.save()
org, _ = Organization.objects.get_or_create(title='Northstar portfolio simulation', created_by=user)
org.add_user(user)
user.active_organization = org
user.save(update_fields=['active_organization'])
print('PORTFOLIO_SESSION=' + json.dumps({'email': user.email, 'password': password, 'version': version('label-studio')}))
'''
    result = subprocess.run(['docker', 'exec', 'northstar-quality-pilot', 'python',
                             'label_studio/manage.py', 'shell', '-c', code],
                            capture_output=True, text=True, check=True)
    line = next(line for line in result.stdout.splitlines() if line.startswith('PORTFOLIO_SESSION='))
    return json.loads(line.split('=', 1)[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label-studio', action='store_true')
    args = parser.parse_args()
    evidence = ROOT / 'reports/evidence'
    evidence.mkdir(exist_ok=True)
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
                                   args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1100}, locale='en-US')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto((ROOT / 'reports/dashboard.html').as_uri(), wait_until='load')
        assert page.locator('details').count() == 30
        assert page.get_by_text('56.7%', exact=True).is_visible()
        assert page.get_by_text('13.3%', exact=True).is_visible()
        page.screenshot(path=str(evidence / 'dashboard-desktop.png'))
        page.locator('summary').first.click()
        assert page.locator('details').first.get_attribute('open') is not None
        assert page.locator('details').first.locator('dd').first.is_visible()
        page.set_viewport_size({'width': 390, 'height': 844})
        page.evaluate('window.scrollTo(0, 0)')
        page.screenshot(path=str(evidence / 'dashboard-mobile.png'))
        overflow = page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
        assert not overflow, 'Page-wide horizontal overflow at mobile size'
        assert not errors, errors
        results['dashboard'] = {'url': 'file://<project>/reports/dashboard.html',
                                'browser_version': browser.version,
                                'cases': 30, 'case_expansion': 'passed',
                                'mobile_viewport': '390x844', 'page_horizontal_overflow': overflow,
                                'page_errors': errors, 'status': 'passed'}
        (evidence / 'browser-verification.json').write_text(json.dumps(results, indent=2) + '\n')
        if args.label_studio:
            account = local_account()
            page.set_viewport_size({'width': 1440, 'height': 1100})
            context.request.get(BASE + '/user/login/')
            login_csrf = next(c['value'] for c in context.cookies(BASE) if c['name'] == 'csrftoken')
            login = context.request.post(BASE + '/user/login/', form={
                'email': account['email'], 'password': account['password'],
                'csrfmiddlewaretoken': login_csrf,
            }, headers={'Referer': BASE + '/user/login/'})
            assert login.ok, 'Local synthetic reviewer login failed'
            page.goto(BASE + '/projects/', wait_until='domcontentloaded')
            csrf = next(c['value'] for c in context.cookies(BASE) if c['name'] == 'csrftoken')
            headers = {'X-CSRFToken': csrf, 'Referer': BASE + '/projects/'}
            response = context.request.post(BASE + '/api/projects/', data={
                'title': 'AI Response Quality Evaluation Pilot',
                'description': 'Independent portfolio simulation; no real model or human-review claim.',
                'label_config': (ROOT / 'label-studio/labeling-config.xml').read_text(),
            }, headers=headers)
            assert response.status == 201, (response.status, response.text()[:500])
            project_id = response.json()['id']
            tasks = json.loads((ROOT / 'label-studio/import-tasks.json').read_text())
            imported = context.request.post(BASE + f'/api/projects/{project_id}/import?return_task_ids=true',
                                            data=tasks, headers=headers)
            assert imported.status == 201, (imported.status, imported.text()[:500])
            summary = imported.json()
            assert summary['task_count'] == 30, summary
            task_ids = summary['task_ids']
            assert len(task_ids) == 30
            # API-assigned IDs are separate from portable task.data.test_id.
            task = context.request.get(BASE + f'/api/tasks/{task_ids[0]}/').json()
            assert task['data']['test_id'] == 'TC-001'
            page.goto(BASE + f'/projects/{project_id}/data?task={task_ids[0]}', wait_until='domcontentloaded')
            page.get_by_text('Primary classification — select exactly one', exact=True).wait_for(timeout=60000)
            page.screenshot(path=str(evidence / 'label-studio-interface.png'), full_page=True)
            for label in ['Correct', 'Partially correct', 'Incorrect', 'Unsupported', 'Yes', 'No']:
                page.get_by_text(re.compile('^' + re.escape(label) + r'(?:\s*\[\d+\])?$')).filter(visible=True).first.wait_for()
            for field in ['question', 'policy_context', 'reference_answer', 'candidate_response']:
                assert page.get_by_text(tasks[0]['data'][field], exact=True).filter(visible=True).last.is_visible()
            page.get_by_text(re.compile(r'^Correct(?:\s*\[\d+\])?$')).filter(visible=True).first.click()
            page.get_by_text(re.compile(r'^No(?:\s*\[\d+\])?$')).filter(visible=True).first.click()
            page.get_by_placeholder('Explain the classification and critical-failure decision with policy references.').fill('UI smoke check only; no annotation submitted and no independent review claimed.')
            page.screenshot(path=str(evidence / 'label-studio-interface.png'), full_page=True)
            results['label_studio'] = {'version': account['version'], 'project_id': project_id,
                'task_count': 30, 'project_create_http': response.status,
                'task_import_http': imported.status, 'portable_id_verified': 'TC-001',
                'question_context_reference_candidate_controls': 'rendered',
                'classification_critical_comments_interaction': 'passed',
                'annotations_submitted': 0, 'status': 'passed',
                'image_digest': 'sha256:afcc516a22775a39d0d66f4c2ddc95d01be3e3d3862b21fcf4f9de34b4ad4e12'}
        browser.close()
    (evidence / 'browser-verification.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
