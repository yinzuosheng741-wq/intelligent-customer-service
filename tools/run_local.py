"""Run the three application services locally with in-memory development storage."""
from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager, suppress
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
RUNTIME = PROJECT / '_runtime'


def environment() -> dict[str, str]:
    from dotenv import dotenv_values
    env = dict(os.environ)
    env.update({key: value for key, value in dotenv_values(PROJECT / '.env').items() if value is not None})
    env.update({
        'STORAGE_MODE': 'memory',
        'VECTOR_BACKEND': 'memory',
        'HOST': '127.0.0.1',
        'PORT': '18000',
        'PI_AGENT_URL': 'http://127.0.0.1:18100',
        'BACKEND_URL': 'http://127.0.0.1:18000',
        'CORS_ORIGINS': 'http://localhost:18080,http://127.0.0.1:18080',
        'UPLOAD_STORAGE_DIR': str(PROJECT / 'local_uploads'),
        'PYTHONUTF8': '1',
        'PYTHONUNBUFFERED': '1',
        'NEXT_TELEMETRY_DISABLED': '1',
    })
    if not env.get('RELAY_API_KEY'):
        env['EMBEDDING_PROVIDER'] = 'hash'
        env['RERANKER_ENABLED'] = 'false'
    return env


def run_backend() -> None:
    os.environ.update(environment())
    sys.path.insert(0, str(PROJECT / 'backend'))
    import uvicorn
    from app.main import app
    from scripts.seed_data import CALENDAR, DEPARTMENTS, GLOSSARY
    from scripts.ingest_department_files import resolve_dept
    from scripts.async_worker import process as process_job

    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with original_lifespan(application):
            container = application.state.container
            for department in DEPARTMENTS:
                await container.store.upsert_department(dict(department))
            for index, term in enumerate(GLOSSARY):
                await container.store.upsert_glossary({'_id': f'local_{index}', **term})
            await container.global_memory.set_calendar(CALENDAR)
            files = sorted((PROJECT / 'department_files').rglob('*.md'))
            for file in files:
                await container.indexer.ingest(file, dept_id=resolve_dept(file), uploaded_by='local_development')
            print(f'Local development knowledge ready: {len(files)} documents.', flush=True)

            async def worker():
                while True:
                    for job in await container.job_queue.next_jobs():
                        try:
                            result = await process_job(container, job)
                            await container.job_queue.finish(job, 'completed', result)
                        except Exception as error:
                            await container.job_queue.finish(job, 'failed', {'error': type(error).__name__})
                    await asyncio.sleep(0.2)

            task = asyncio.create_task(worker())
            try:
                yield
            finally:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    app.router.lifespan_context = lifespan
    uvicorn.run(app, host='127.0.0.1', port=18000)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--stop', action='store_true', help='Stop services started by this launcher')
    args = parser.parse_args()
    RUNTIME.mkdir(exist_ok=True)
    record = RUNTIME / 'local-services.json'
    if args.backend:
        run_backend()
        return
    if args.stop:
        if record.exists():
            for service in json.loads(record.read_text(encoding='utf-8')):
                try:
                    os.kill(service['pid'], signal.SIGTERM)
                    print(f"Stopped {service['name']} (PID {service['pid']}).")
                except ProcessLookupError:
                    pass
            record.unlink()
        return
    if record.exists():
        raise SystemExit('A local service record exists. Use --stop before restarting.')
    node = shutil.which('node')
    if not node:
        raise SystemExit('Node.js is required.')
    env = environment()
    services = [
        ('pi', [node, 'dist/index.js'], PROJECT / 'services/pi-agent', {**env, 'PORT': '18100'}),
        ('backend', [sys.executable, str(Path(__file__).resolve()), '--backend'], PROJECT, env),
        ('web', [node, 'node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1', '--port', '18080'], PROJECT / 'web', env),
    ]
    records = []
    flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
    for name, command, cwd, service_env in services:
        with (RUNTIME / f'{name}.log').open('ab') as log:
            process = subprocess.Popen(command, cwd=cwd, env=service_env, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT, creationflags=flags,
                                       start_new_session=os.name != 'nt')
        records.append({'name': name, 'pid': process.pid})
        record.write_text(json.dumps(records, indent=2), encoding='utf-8')
    print('Local services started. Knowledge is loaded during backend startup.')
    print('UI: http://127.0.0.1:18080  API: http://127.0.0.1:18000/docs')
    print('Logs: _runtime/backend.log, _runtime/pi.log, _runtime/web.log')


if __name__ == '__main__':
    main()
