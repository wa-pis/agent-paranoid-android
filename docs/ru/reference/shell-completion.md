# Дополнение команд оболочки

[English](../../reference/shell-completion.md) · Русский

Completion создаётся установленным parser, поэтому соответствует версии, aliases и options текущего пакета. Выполните одну команду для своей оболочки; она печатает сценарий и не меняет startup files:

```bash
test-data-agent completion bash
test-data-agent completion zsh
test-data-agent completion fish
test-data-agent completion powershell
```

Установка полученного сценария зависит от оболочки и не выполнялась в этом аудите. Сначала проверьте test-data-agent --version. Не подключайте сценарий от другой версии без review.
