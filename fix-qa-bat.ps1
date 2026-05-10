$content = "@echo off
cd /d D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main
opencode run --file prompts\qa-agent-prompt.md --dir . `"请读取并执行附件中的指令`" -m minimax-cn-coding-plan/MiniMax-M2.7"
[System.IO.File]::WriteAllText("D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main\run-qa-agent.bat", $content, [System.Text.Encoding]::ASCII)