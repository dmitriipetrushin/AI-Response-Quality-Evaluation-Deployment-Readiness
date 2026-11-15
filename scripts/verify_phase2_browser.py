#!/usr/bin/env python3
"""Optional genuine Chrome interaction with the assistant and separate Label Studio project."""
import argparse
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from src.assistant import ROOT, load_config
from scripts.verify_local_browser import local_account


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label-studio', action='store_true')
    args = parser.parse_args()
    config = load_config()
    base = f"http://{config['host']}:{config['port']}"
    evidence = ROOT / 'reports/phase-2-evidence'
    evidence.mkdir(exist_ok=True)
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
                                   args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1100})
        page = context.new_page()
        page_errors = []; remote_requests = []
        page.on('pageerror', lambda error: page_errors.append(str(error)))
        page.on('request', lambda req: remote_requests.append(req.url) if not req.url.startswith(base + '/') else None)
        page.goto(base, wait_until='networkidle')
        page.get_by_text('Local model ready', exact=False).wait_for()
        page.get_by_role('button', name='Password sharing', exact=True).click()
        question = page.locator('#question').input_value()
        started = time.perf_counter()
        with page.expect_response(lambda response: response.url == base + '/api/ask', timeout=610000) as pending:
            page.get_by_role('button', name='Ask assistant', exact=False).click()
        response = pending.value
        assert response.status == 200, response.text()
        result = response.json()
        page.locator('#answer-panel').wait_for()
        assert page.locator('#answer').inner_text() == result['answer']
        assert result['response_source'] == 'ollama_local_inference'
        assert result['token_usage']['eval_count'] > 0
        page.locator('#citations summary').first.wait_for()
        page.locator('#citations summary').first.click()
        assert 'POL-' in page.locator('#citations').inner_text()
        page.screenshot(path=str(evidence / 'assistant-desktop.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(evidence / 'assistant-mobile.png'), full_page=True)
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not page_errors, page_errors
        assert not remote_requests, remote_requests
        results['assistant'] = {'question': question, 'response': result, 'http_status': response.status,
             'browser_elapsed_seconds': round(time.perf_counter() - started, 6),
             'browser_version': browser.version, 'example_button': 'passed', 'submit_button': 'passed',
             'policy_expansion': 'passed', 'mobile_page_overflow': False, 'page_errors': list(page_errors),
             'remote_requests': list(remote_requests), 'status': 'passed'}
        page.set_viewport_size({'width': 1440, 'height': 1100})
        page.goto(base + '/reports/dashboard.html', wait_until='load')
        assert page.get_by_role('heading', name='Synthetic Evaluation Baseline', exact=True).is_visible()
        assert page.get_by_role('heading', name='Real LLM Evaluation', exact=True).is_visible()
        assert page.locator('details').count() == 30
        page.locator('#real-llm-evaluation').scroll_into_view_if_needed()
        page.screenshot(path=str(evidence / 'combined-dashboard.png'))
        results['dashboard'] = {'synthetic_and_real_sections': 'passed', 'synthetic_case_count': 30,
             'assistant_link': page.get_by_role('link', name='Open interactive AI assistant').get_attribute('href'), 'status': 'passed'}
        (evidence / 'browser-verification.json').write_text(json.dumps(results, indent=2) + '\n')
        if args.label_studio:
            ls = 'http://127.0.0.1:8087'
            account = local_account()
            context.request.get(ls + '/user/login/')
            csrf = next(c['value'] for c in context.cookies(ls) if c['name'] == 'csrftoken')
            context.request.post(ls + '/user/login/', form={'email': account['email'], 'password': account['password'],
                                 'csrfmiddlewaretoken': csrf}, headers={'Referer': ls + '/user/login/'})
            page.goto(ls + '/projects/', wait_until='domcontentloaded')
            csrf = next(c['value'] for c in context.cookies(ls) if c['name'] == 'csrftoken')
            headers = {'X-CSRFToken': csrf, 'Referer': ls + '/projects/'}
            prior = context.request.get(ls + '/api/projects/').json()
            prior_projects = prior if isinstance(prior, list) else prior.get('results', [])
            prior_ids = [p['id'] for p in prior_projects]
            response = context.request.post(ls + '/api/projects/', data={
                'title': 'Northstar real LLM evaluation (provisional review)',
                'description': 'Actual local-model outputs. Unannotated; no independent review claimed.',
                'label_config': (ROOT / 'label-studio/real-model-labeling-config.xml').read_text(),
            }, headers=headers)
            assert response.status == 201, (response.status, response.text()[:500])
            project_id = response.json()['id']
            assert project_id not in prior_ids
            tasks = json.loads((ROOT / 'label-studio/real-model-import-tasks.json').read_text())
            imported = context.request.post(ls + f'/api/projects/{project_id}/import?return_task_ids=true', data=tasks, headers=headers)
            assert imported.status == 201, (imported.status, imported.text()[:500])
            summary = imported.json()
            assert summary['task_count'] == 30
            for task_id, expected in zip(summary['task_ids'], tasks):
                actual = context.request.get(ls + f'/api/tasks/{task_id}/').json()
                assert actual['data']['candidate_response'] == expected['data']['candidate_response']
                assert actual['data']['response_source'] == 'ollama_local_inference'
                assert not actual['annotations']
            page.goto(ls + f"/projects/{project_id}/data?task={summary['task_ids'][0]}", wait_until='domcontentloaded')
            page.get_by_text('Candidate response — actual local-model inference', exact=True).wait_for(timeout=60000)
            page.get_by_text(tasks[0]['data']['candidate_response'], exact=True).filter(visible=True).last.wait_for()
            page.screenshot(path=str(evidence / 'label-studio-real-model.png'), full_page=True)
            after = context.request.get(ls + '/api/projects/').json()
            after_projects = after if isinstance(after, list) else after.get('results', [])
            assert set(prior_ids).issubset({p['id'] for p in after_projects})
            results['label_studio'] = {'version': account['version'], 'new_project_id': project_id,
                'existing_project_ids_preserved': prior_ids, 'task_count': 30, 'all_imported_answers_verified': True,
                'annotations_submitted': 0, 'interface_rendered': True, 'status': 'passed'}
        browser.close()
    (evidence / 'browser-verification.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: {field: value for field, value in v.items() if field != 'response'} for k,v in results.items()}, indent=2))


if __name__ == '__main__':
    main()
