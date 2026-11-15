#!/usr/bin/env python3
"""Optional Chrome/Playwright verification, preserving historical browser evidence.

Run after the selected app and existing Label Studio container have started:
.venv-label-studio/bin/python scripts/verify_phase3_browser.py --label-studio
No annotation is submitted. Only a separate Phase-3 project may be created/imported.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.verify_local_browser import local_account
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
APP = 'http://127.0.0.1:8000'
LS = 'http://127.0.0.1:8087'
TITLE = 'Phase 3 — Selected real local model — independent review pending'


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label-studio', action='store_true')
    args = parser.parse_args()
    evidence = ROOT/'reports/phase-3-evidence'
    selection = json.loads((ROOT/'experiments/phase-3/selection.json').read_text())
    metrics = json.loads((ROOT/'reports/phase-3-metrics.json').read_text())
    results = {'quality_status': 'Provisional agent-assisted reviews; no independent human annotations.'}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
                                   args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width':1440,'height':1100}, locale='en-US')
        page = context.new_page(); errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(APP, wait_until='networkidle')
        page.locator('#service-status').filter(has_text='Local model ready').wait_for()
        question = 'How many annual leave days does the handbook provide?'
        page.locator('#question').fill(question)
        with page.expect_response(lambda r:r.url.endswith('/api/ask') and r.request.method=='POST', timeout=240000) as event:
            page.locator('#ask-button').click()
        response = event.value; body = response.json()
        assert response.ok and body['model'] == selection['config']['model']
        assert body['prompt_version'] == selection['config']['prompt_version']
        assert body['response_source'] == 'ollama_local_inference'
        assert body['token_usage']['eval_count'] > 0
        assert not any(k in body for k in ['raw_response','generated_content','generation_attempts'])
        page.locator('#answer-panel').wait_for(state='visible')
        assert page.locator('#answer').inner_text() == body['answer']
        assert selection['config']['model'] in page.locator('#answer-meta').inner_text()
        assert 'Profile: '+selection['config']['prompt_version'] in page.locator('#answer-meta').inner_text()
        citations = page.locator('#citations details')
        if citations.count():
            citations.first.locator('summary').click()
            page.wait_for_function("!document.querySelector('#citations pre').textContent.startsWith('Loading')")
            assert 'POL-' in citations.first.inner_text()
        page.screenshot(path=str(evidence/'app-desktop.png'), full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
        page.screenshot(path=str(evidence/'app-mobile.png'), full_page=True)
        # Real server input error; neither a mock model nor a synthetic successful reply.
        bad = context.request.post(APP+'/api/ask',data={'question':''})
        assert bad.status == 400
        results['application'] = {'status':'passed','question':question,'response':body,
            'empty_question_http':bad.status,'desktop_and_mobile':True,'citation_controls':citations.count()}
        page.set_viewport_size({'width':1440,'height':1100})
        for url in [(ROOT/'reports/phase-3-dashboard.html').as_uri(), APP+'/reports/phase-3-dashboard.html']:
            page.goto(url,wait_until='networkidle')
            assert page.locator('#experiment-rows tr').count() == len(metrics['experiments'])
            page.locator('#split-filter').select_option('validation')
            assert page.locator('#experiment-rows tr').count() == 5
            page.locator('#model-filter').select_option('llama3.2:3b')
            assert page.locator('#experiment-rows tr').count() == 1
            assert 'llama3.2:3b' in page.locator('#resource-summary').inner_text()
            page.locator('#model-filter').select_option('')
            page.locator('#split-filter').select_option('all')
            assert page.locator('#experiment-rows tr').count() == 1
            assert page.locator('#difficulty-rows tr').count() == 3
            assert page.locator('#category-rows tr').count() > 0
            assert 'Selected configuration' in page.locator('#heldout-summary').inner_text()
        page.screenshot(path=str(evidence/'comparison-desktop.png'), full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
        page.screenshot(path=str(evidence/'comparison-mobile.png'), full_page=True)
        page.goto(APP+'/reports/dashboard.html',wait_until='load')
        assert page.locator('details').count() == 30
        assert page.get_by_text('56.7%',exact=True).is_visible()
        assert page.locator('a[href="phase-3-dashboard.html"]').count() > 0
        assert not errors, errors
        results['dashboard'] = {'status':'passed','file_and_http':True,'filters_and_grouping':'passed',
            'historical_details':30,'mobile_overflow':False,'page_errors':errors,'browser_version':browser.version}
        if args.label_studio:
            account = local_account()
            context.request.get(LS+'/user/login/')
            csrf = next(c['value'] for c in context.cookies(LS) if c['name']=='csrftoken')
            login = context.request.post(LS+'/user/login/',form={'email':account['email'],
                'password':account['password'],'csrfmiddlewaretoken':csrf},headers={'Referer':LS+'/user/login/'})
            assert login.ok
            headers = {'X-CSRFToken':next(c['value'] for c in context.cookies(LS) if c['name']=='csrftoken'),
                       'Referer':LS+'/projects/'}
            def projects():
                res = context.request.get(LS+'/api/projects/?page_size=100')
                assert res.ok
                value=res.json(); return value['results'] if isinstance(value,dict) else value
            def snapshot(ids):
                output={}
                for pid in ids:
                    r=context.request.get(LS+f'/api/projects/{pid}/export?exportType=JSON&download_all_tasks=true')
                    assert r.ok,(pid,r.status)
                    output[str(pid)]=fingerprint(r.json())
                return output
            old=projects(); historical=[x['id'] for x in old if x['title']!=TITLE]
            before=snapshot(historical)
            existing=[x for x in old if x['title']==TITLE]
            tasks=json.loads((ROOT/'label-studio/phase-3-import-tasks.json').read_text())
            assert len(tasks)==100 and all('annotations' not in t and 'predictions' not in t for t in tasks)
            if existing:
                assert len(existing)==1
                project_id=existing[0]['id']
                exported=context.request.get(LS+f'/api/projects/{project_id}/export?exportType=JSON&download_all_tasks=true').json()
                assert len(exported)==100
                task_ids=[x['id'] for x in exported]
            else:
                created=context.request.post(LS+'/api/projects/',data={'title':TITLE,
                    'description':'Actual final inference; no prefilled labels or human-review claim.',
                    'label_config':(ROOT/'label-studio/phase-3-labeling-config.xml').read_text()},headers=headers)
                assert created.status==201,created.text()[:400]
                project_id=created.json()['id']
                imported=context.request.post(LS+f'/api/projects/{project_id}/import?return_task_ids=true',data=tasks,headers=headers)
                assert imported.status==201,imported.text()[:400]
                assert imported.json()['task_count']==100
                task_ids=imported.json()['task_ids']
            exported=context.request.get(LS+f'/api/projects/{project_id}/export?exportType=JSON&download_all_tasks=true').json()
            assert len(exported)==100
            expected={t['data']['test_id']:t['data'] for t in tasks}
            assert all(t['data']==expected[t['data']['test_id']] for t in exported)
            assert all(not t.get('annotations') and not t.get('predictions') for t in exported)
            page.set_viewport_size({'width':1440,'height':1100})
            page.goto(LS+f'/projects/{project_id}/data?task={task_ids[0]}',wait_until='domcontentloaded')
            page.get_by_text('Actual model answer',exact=True).wait_for(timeout=60000)
            for label in ['Correct','Partially correct','Incorrect','Unsupported','Yes','No','Low','Medium','High','Critical']:
                page.get_by_text(re.compile('^'+re.escape(label)+r'(?:\s*\[\d+\])?$')).filter(visible=True).first.wait_for()
            page.get_by_placeholder(re.compile('Explain the decision')).fill('UI smoke check only; no independent annotation submitted.')
            page.screenshot(path=str(evidence/'label-studio-phase3.png'),full_page=True)
            after=snapshot(historical); assert before==after,'Historical exports changed'
            updated=context.request.get(LS+f'/api/projects/{project_id}/export?exportType=JSON&download_all_tasks=true').json()
            assert len(updated)==100 and all(not t.get('annotations') for t in updated)
            results['label_studio']={'status':'passed','version':account['version'],'project_id':project_id,
                'tasks':100,'annotations_submitted':0,'tasks_with_annotations':0,'controls_rendered':True,
                'historical_project_ids':historical,'historical_export_sha256_before':before,
                'historical_export_sha256_after':after,'exact_response_bindings_verified':100}
        browser.close()
    (evidence/'browser-verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v.get('status') for k,v in results.items() if isinstance(v,dict)},indent=2))


if __name__=='__main__': main()
