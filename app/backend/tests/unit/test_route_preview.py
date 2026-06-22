from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.unified_generation_routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_route_preview_returns_non_production_estimate():
    resp = client.post('/api/v1/generation/route-preview', json={
        'prompt': '为一款橙色咖啡杯生成电商主图',
        'modality': 'image',
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data['is_preview'] is True
    assert data['productionRoute'] is False
    assert data['recommendedRoute']['provider']
    assert data['recommendedRoute']['modality'] == 'image'
    assert data['estimatedCost']['amount'] >= 0
    assert data['estimatedCost']['currency'] == 'USD'
    assert data['estimatedCost']['source'] == 'moyag_inventory'


def test_route_preview_respects_optional_model_key():
    resp = client.post('/api/v1/generation/route-preview', json={
        'prompt': '生成一条 5 秒产品视频',
        'modality': 'video',
        'modelKey': 'runway:video',
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data['recommendedRoute']['modelKey'] == 'runway:video'
    assert data['recommendedRoute']['provider'] == 'runway'
    assert data['recommendedRoute']['modality'] == 'video'


def test_route_preview_rejects_empty_prompt():
    resp = client.post('/api/v1/generation/route-preview', json={'prompt': '   '})

    assert resp.status_code == 422


def test_route_preview_returns_image_plan_steps():
    resp = client.post('/api/v1/generation/route-preview', json={
        'prompt': '生成一张白底产品图',
        'modality': 'image',
    })

    assert resp.status_code == 200
    plan = resp.json()['plan']
    assert plan['type'] == 'single_asset'
    assert [step['id'] for step in plan['steps']] == ['analyze', 'route', 'generate_image', 'deliver']
    assert all(step['productionRoute'] is False for step in plan['steps'])


def test_route_preview_returns_video_plan_steps():
    resp = client.post('/api/v1/generation/route-preview', json={
        'prompt': '生成一条 5 秒产品视频',
        'modality': 'video',
    })

    assert resp.status_code == 200
    plan = resp.json()['plan']
    assert plan['type'] == 'multi_step_video'
    assert [step['id'] for step in plan['steps']] == ['analyze', 'route', 'storyboard', 'generate_video', 'deliver']


def test_route_preview_halts_when_over_budget():
    resp = client.post('/api/v1/generation/route-preview', json={
        'prompt': '生成一张白底产品图',
        'modality': 'image',
        'maxBudget': 0.001,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data['budgetGate']['halted'] is True
    assert data['budgetGate']['reason'] == 'over_budget'
    assert data['productionRoute'] is False


def test_cancel_processing_task_has_zero_spend():
    from app.api.unified_generation_routes import _async_gen_tasks

    _async_gen_tasks['preview-cancel-test'] = {'status': 'processing'}
    resp = client.post('/api/v1/generation/task/preview-cancel-test/cancel')

    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'cancelled'
    assert data['spent']['amount'] == 0
    assert data['spent']['currency'] == 'USD'
    assert _async_gen_tasks['preview-cancel-test']['status'] == 'cancelled'
    del _async_gen_tasks['preview-cancel-test']
