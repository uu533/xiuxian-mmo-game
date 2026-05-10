$content = "@echo off
cd /d D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main
opencode run `"请读取并执行附件中的指令`" --file prompts\dev-agent-prompt.md --dir . -m minimax-cn-coding-plan/MiniMax-M2.7"
[System.IO.File]::WriteAllText("D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main\run-dev-agent.bat", $content, [System.Text.Encoding]::ASCII)