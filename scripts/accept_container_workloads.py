"""Run bounded fictional CLI/MCP workloads in an already built hardened image."""
from __future__ import annotations

import argparse
import json
import os
import selectors
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any


BOOTSTRAP = '''
import json, os
from pathlib import Path
assert os.geteuid() == 65532
root = Path('/workspace')
(root / 'source.csv').write_text('id,quantity,label\\n1,2,fictional_source_only\\n2,3,fictional_source_only\\n')
spec = {'entities': [{'name': 'records', 'row_count': 4, 'primary_key': 'id', 'fields': [
 {'name': 'id', 'data_type': 'integer', 'is_identifier': True, 'distribution': {'kind': 'synthetic_identifier'}},
 {'name': 'quantity', 'data_type': 'integer', 'distribution': {'kind': 'numeric', 'min_value': 2, 'max_value': 4}},
 {'name': 'label', 'data_type': 'string', 'distribution': {}}]}],
 'generation_settings': {'seed': 17, 'output_format': 'json'}}
(root / 'spec.json').write_text(json.dumps(spec))
'''
CLI_WORKLOAD = BOOTSTRAP + '''
import hashlib, subprocess
for output_format in ('json', 'csv', 'sql'):
 command = ['test-data-agent', 'generate', '/workspace/spec.json', '--seed', '17', '--format', output_format]
 for suffix in ('first', 'replay'):
  output = '/workspace/' + output_format + '-' + suffix
  run = subprocess.run(command + ['--output', output], capture_output=True, text=True, timeout=60)
  assert run.returncode == 0, 'CLI generation failed: ' + output_format
  manifest = json.loads((Path(output) / 'generation_manifest.json').read_text())
  assert manifest['synthetic'] and not manifest['source_rows_copied'] and manifest['row_counts'] == {'records': 4}
  check = subprocess.run(['test-data-agent', 'validate', '/workspace/spec.json', output], capture_output=True, text=True, timeout=60)
  assert check.returncode == 0, 'CLI validation failed: ' + output_format
  rows = (Path(output) / ('records.' + output_format)).read_bytes()
  assert b'fictional_source_only' not in rows
  if suffix == 'first':
   first = rows
  else:
   assert rows == first, 'seed replay differs'
missing = subprocess.run(['test-data-agent', 'generate', '/workspace/spec.json', '--format', 'parquet', '--output', '/workspace/missing-parquet'], capture_output=True, text=True, timeout=60)
assert missing.returncode != 0 and 'parquet' in (missing.stdout + missing.stderr).lower()
assert not Path('/workspace/missing-parquet').exists()
print(json.dumps({'formats': ['json', 'csv', 'sql'], 'seed_replay': True, 'missing_parquet_refused': True, 'synthetic': True, 'sha256': hashlib.sha256(first).hexdigest()}))
'''


def container_arguments(image: str, target: str, platform: str, name: str) -> list[str]:
    arguments = [
        'docker', 'run', '--rm', '-i', '--name', name, '--platform', platform,
        '--read-only', '--network', 'none', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--pids-limit', '128',
        '--memory', '512m', '--cpus', '2',
        '--tmpfs', '/tmp:size=64m,noexec,nosuid,nodev',
    ]
    if target != 'trino-mcp':
        arguments += ['--tmpfs', '/workspace:size=1g,nosuid,nodev,uid=65532,gid=65532']
    if target == 'trino-mcp':
        for key, value in {
            'TRINO_HOST': 'trino.example.test', 'TRINO_PORT': '443',
            'TRINO_USER': 'container_check', 'TRINO_HTTP_SCHEME': 'https',
            'TRINO_ALLOWED_CATALOGS': 'example', 'TRINO_ALLOWED_SCHEMAS': 'synthetic',
        }.items():
            arguments += ['--env', f'{key}={value}']
    return arguments + ['--entrypoint', 'python', image, '-c']


class StdioClient:
    def __init__(self, command: list[str]) -> None:
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)
        self.sequence = 0
        self.response_timeout = 90.0
        self.frame_limit = 1024 * 1024
        self.buffer = bytearray()

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.sequence += 1
        assert self.process.stdin is not None and self.process.stdout is not None
        message = {'jsonrpc': '2.0', 'id': self.sequence, 'method': method, 'params': params}
        self.process.stdin.write((json.dumps(message) + '\n').encode())
        self.process.stdin.flush()
        deadline = time.monotonic() + self.response_timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while b'\n' not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(timeout=remaining):
                    raise TimeoutError('container MCP response deadline exceeded')
                chunk = os.read(self.process.stdout.fileno(), min(65536, self.frame_limit + 1 - len(self.buffer)))
                if not chunk:
                    raise EOFError('container MCP response channel closed')
                self.buffer.extend(chunk)
                if len(self.buffer) > self.frame_limit:
                    raise ValueError('container MCP response frame limit exceeded')
        line, _, remainder = self.buffer.partition(b'\n')
        self.buffer = bytearray(remainder)
        response: dict[str, Any] = json.loads(line)
        assert response.get('id') == self.sequence, 'unexpected MCP response'
        return response

    def initialize(self) -> None:
        response = self.request('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                                               'clientInfo': {'name': 'fictional-container-acceptance', 'version': '1'}})
        assert 'result' in response
        assert self.process.stdin is not None
        self.process.stdin.write((json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n').encode())
        self.process.stdin.flush()

    def call(self, name: str, arguments: dict[str, Any], *, expect_error: bool = False) -> dict[str, Any]:
        response = self.request('tools/call', {'name': name, 'arguments': arguments})
        result = response.get('result', {})
        failed = 'error' in response or result.get('isError', False)
        assert failed == expect_error, 'unexpected tool outcome: ' + name
        encoded = json.dumps(response)
        assert 'fictional_source_only' not in encoded, 'source literal disclosed'
        if expect_error:
            return {}
        structured = result.get('structuredContent')
        if isinstance(structured, dict):
            return structured
        content = result['content']
        payload: dict[str, Any] = json.loads(''.join(item.get('text', '') for item in content))
        return payload

    def close(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=10)


def mcp_workload(arguments: list[str], target: str) -> dict[str, Any]:
    executable = 'test-data-agent-mcp-generator' if target == 'generator-mcp' else 'test-data-agent-mcp-trino'
    bootstrap = BOOTSTRAP if target == 'generator-mcp' else 'import os\nassert os.geteuid() == 65532\n'
    client = StdioClient(arguments + [bootstrap + f'\nos.execlp({executable!r}, {executable!r})'])
    try:
        client.initialize()
        response = client.request('tools/list', {})
        names = {tool['name'] for tool in response['result']['tools']}
        assert 'transform_approve' not in names and 'run_safe_select' not in names
        if target == 'generator-mcp':
            assert {'profile_csv', 'infer_dataset_spec', 'generate_dataset', 'validate_dataset', 'export_dataset'} <= names
            client.call('profile_csv', {'input_path': 'source.csv', 'output_path': 'profile.json'})
            client.call('infer_dataset_spec', {'profile_path': 'profile.json', 'output_path': 'inferred.yaml', 'count': 4})
            client.call('generate_dataset', {'spec_path': 'spec.json', 'output_folder': 'generated', 'seed': 17})
            result = client.call('validate_dataset', {'spec_path': 'spec.json', 'rows_folder': 'generated'})
            assert result['validation']['valid']
            client.call('export_dataset', {'spec_path': 'spec.json', 'output_folder': 'exported', 'output_format': 'csv', 'seed': 17})
            client.call('generate_dataset', {'spec_path': 'spec.json', 'output_folder': 'generated'}, expect_error=True)
            client.call('profile_csv', {'input_path': '/etc/passwd', 'output_path': 'blocked.json'}, expect_error=True)
        else:
            assert {'list_catalogs', 'list_schemas', 'profile_table_safe'} <= names
            client.call('list_schemas', {'catalog': 'excluded'}, expect_error=True)
        return {'tool_count': len(names), 'actual_requests': True, 'network': 'none'}
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--target', choices=('cli', 'generator-mcp', 'trino-mcp'), required=True)
    parser.add_argument('--platform', choices=('linux/amd64', 'linux/arm64'), required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    name = 'apa-acceptance-' + uuid.uuid4().hex[:12]
    started = time.monotonic()
    record: dict[str, Any] = {'target': args.target, 'platform': args.platform, 'image': args.image}
    try:
        inspect = subprocess.run(['docker', 'image', 'inspect', args.image], capture_output=True, text=True, check=True, timeout=30)
        image = json.loads(inspect.stdout)[0]
        assert image['Config']['User'] == '65532:65532'
        assert image['Architecture'] == args.platform.split('/')[1]
        record['image_id'] = image['Id']
        record['source_sha'] = image['Config']['Labels']['org.opencontainers.image.revision']
        arguments = container_arguments(args.image, args.target, args.platform, name)
        if args.target == 'cli':
            run = subprocess.run(arguments + [CLI_WORKLOAD], capture_output=True, text=True, timeout=240)
            assert run.returncode == 0, 'container CLI workload failed'
            record['result'] = json.loads(run.stdout)
        else:
            record['result'] = mcp_workload(arguments, args.target)
        record['status'] = 'passed'
    except Exception as exc:
        record.update(status='failed', reason=type(exc).__name__)
        raise
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20)
        record['duration_seconds'] = round(time.monotonic() - started, 3)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
