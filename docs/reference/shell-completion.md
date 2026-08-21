# Shell Completion

Generate completion from the installed parser so commands, aliases, and options
match the exact package version:

```bash
test-data-agent completion bash > test-data-agent.bash
test-data-agent completion zsh > _test-data-agent
test-data-agent completion fish > test-data-agent.fish
test-data-agent completion powershell > test-data-agent.ps1
```

Source or install the generated file according to your shell. The command does
not create or edit shell configuration.
