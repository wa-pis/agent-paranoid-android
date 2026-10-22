# Работа в контейнерах

[English](../../operations/containers.md) · Русский

Контейнеры — отдельный способ запуска CLI/MCP worker. Для локального Python обычный путь — PyPI. Образы 1.6.0 опубликованы с [проверяемыми digest/signature](../../release-evidence-1.6.0.md).

| Образ GHCR, префикс ghcr.io/wa-pis/ | Entrypoint | Возможности |
| --- | --- | --- |
| agent-paranoid-android-cli | test-data-agent | Core CSV/JSON |
| agent-paranoid-android-generator-mcp | test-data-agent-mcp-generator | Core + MCP |
| agent-paranoid-android-trino-mcp | test-data-agent-mcp-trino | Core + MCP + Trino/SQLGlot |

Выберите tag 1.6.0, затем разрешите и проверьте immutable digest. Latest, 1 и 1.6 — mutable aliases. Публикуются linux/amd64 и linux/arm64; PyArrow не входит, для Parquet используйте Python extra.

## Локальная сборка

Из корня checkout можно собрать только нужный target; Docker-выполнение здесь не проверялось:

```bash
docker build --target cli -t agent-paranoid-android:cli .
docker build --target generator-mcp -t agent-paranoid-android:generator-mcp .
docker build --target trino-mcp -t agent-paranoid-android:trino-mcp .
```

Compose использует non-root UID/GID (по умолчанию 65532), read-only root, dropped capabilities, no-new-privileges, конечные CPU/memory/process/tmp limits и не публикует ports. Writable workspace/audit mounts и отдельные owner-only secret files готовятся администратором. CONTAINER_UID/GID не могут быть нулевыми. Не коммитьте workspace, audit и secrets.

Generator получает /workspace и /audit без network. Он подходит для synthetic/local-file работы и не может молча получить DB capture access. Trino worker имеет outbound network, узкие HTTPS allowlists и read-only роль; generator workspace ему не монтируется.

MCP client запускает docker compose run --rm -T generator-mcp через stdio. Это не HTTP endpoint. Deadline TEST_DATA_AGENT_MCP_MAX_INVOCATION_SECONDS по умолчанию 120 секунд; остальные budgets остаются независимыми.

## Audit и проверка образа

У workers разные ключи и audit mounts. Key file передаётся через /run/secrets, не image metadata или открытый client config. Перед rotation остановите соответствующего writer.

Перед запуском проверьте digest через Cosign, GitHub attestation и SBOM по точным командам [оригинального руководства — English](../../operations/containers.md#verify-a-published-image). Они требуют опубликованного digest, не placeholder. Health проверяет только локальные dependencies, non-root, workspace и configuration; он не соединяется с Trino и не читает набор.
