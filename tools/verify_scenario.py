"""Verify customer-service routing, citations and workflows without external models."""
from pathlib import Path
import asyncio, json, os, sys

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'backend'))
os.environ.update(STORAGE_MODE='memory',VECTOR_BACKEND='memory',EMBEDDING_PROVIDER='hash',EMBEDDING_DIM='128',PI_AGENT_ENABLED='false',RERANKER_ENABLED='false',DEEPSEEK_API_KEY='',RELAY_API_KEY='',UPLOAD_STORAGE_DIR=str(PROJECT/'local_uploads'))

async def main():
    from fastapi.testclient import TestClient
    from app.main import app
    from scripts.seed_data import DEPARTMENTS,GLOSSARY,CALENDAR
    from scripts.ingest_department_files import resolve_dept
    from app.loop.default_skills import DEFAULT_SKILLS
    from app.harness.agents.intent_agent import IntentAgent
    report={'mode':'offline_memory_hash_no_llm','checks':{}}
    with TestClient(app) as client:
        c=app.state.container
        for d in DEPARTMENTS:await c.store.upsert_department(d)
        for i,g in enumerate(GLOSSARY):await c.store.upsert_glossary({'_id':str(i),**g})
        await c.global_memory.set_calendar(CALENDAR)
        docs=[]
        for p in sorted((PROJECT/'department_files').rglob('*.md')):
            dept=resolve_dept(p)
            assert dept!='dept_all'
            doc=await c.indexer.ingest(p,dept_id=dept,uploaded_by='scenario_verification')
            assert doc['vector_status']=='ready' and doc['chunk_count']>0
            docs.append(doc)
        report['checks']['ingest_documents']=len(docs)
        # Run every real scenario case through automatic routing and the normal orchestrator.
        cases=json.loads((PROJECT/'backend/evaluation/real_document_qa.json').read_text(encoding='utf-8'))
        rows=[]
        for case in cases:
            route=await c.dept_router.route(case['query'])
            assert case['dept_id'] in route['dept_ids'],(case['query'],route)
            fallback=IntentAgent._keyword_fallback(case['query'])
            assert case['dept_id'] in fallback.depts
            answer=await c.orchestrator.answer(case['query'],user_id='student')
            assert answer['answer'] and answer.get('citations'),case['id']
            for citation in answer['citations']:
                doc=await c.store.get_document(citation['doc_id'])
                assert doc and doc['status']=='active'
                assert citation['snippet']
            cited_files=[(await c.store.get_document(x['doc_id']))['source']['file_name'] for x in answer['citations']]
            assert set(cited_files)&set(case['relevant_files']),case['id']
            rows.append({'id':case['id'],'route_depts':route['dept_ids'],'citations':len(answer['citations']),'cited_files':cited_files,'answer':answer['answer']})
        report['checks']['scenario_qa']=rows
        # Exercise a genuinely unsupported entity query; there is no source for it.
        hits=await c.retrieval_agent.retrieve(['ZXQ-NEVER-EXISTS-9742 的实时防伪查询结果'],['dept_all'],top_k=5)
        report['checks']['unsupported_query_hits']=len(hits)
        skills=await c.store.list_skills(status='active')
        assert len(skills)==3
        report['checks']['baseline_skills']=len(skills)
        workflow_query='商品破损如何申请理赔？'
        matched=await c.skill_executor.matching(workflow_query,['dept_zfxy'])
        plan=await c.skill_executor.prepare(workflow_query,[workflow_query],matched,'skill-demo','student')
        assert plan.top_k==7 and len(plan.queries)>1 and plan.instructions
        assert plan.execution_ids
        report['checks']['claim_skill_workflow']={'top_k':plan.top_k,'expanded_queries':plan.queries,'instructions':plan.instructions,'execution_records':len(plan.execution_ids)}
        catalog=json.loads((PROJECT/'scenario/capability_catalog.json').read_text(encoding='utf-8'))
        assert len(catalog)==23 and all(x['status']=='knowledge_only_not_registered' for x in catalog)
        report['checks']['capability_catalog']=23
        assert client.get('/healthz').status_code==200
        login=client.post('/api/v1/auth/login',json={'username':'student','password':'student123'})
        assert login.status_code==200,login.text
        token=login.json()['data']['token']
        response=client.post('/api/v1/chat',headers={'Authorization':'Bearer '+token},json={'query':cases[0]['query']})
        assert response.status_code==200 and response.json()['data']['citations'],response.text
        report['checks']['http_login_and_chat']='passed'
        print('Scenario checks passed',flush=True)
    (PROJECT/'scenario/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report['checks'].items() if k not in ['scenario_qa','claim_skill_workflow']},ensure_ascii=True))

if __name__=='__main__':asyncio.run(main())
