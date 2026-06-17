# agent-skills

Agent Skill を root 直下に並べる公開用リポジトリです。

方針は固定です。

- skill は `<skill-name>/SKILL.md`
- `skills/` のような中間ディレクトリは作らない
- 分類は README の表と命名で扱う

## Repository Layout

```txt
agent-skills/
├── README.md
├── agentskills-authoring/
│   └── SKILL.md
├── conventional-commit/
│   └── SKILL.md
├── github-project-ops/
│   └── SKILL.md
├── package.json
├── lefthook.yml
└── commitlint.config.ts
```

## Skills

| Skill                   | Area           | Use case                                                                                              |
| ----------------------- | -------------- | ----------------------------------------------------------------------------------------------------- |
| `agentskills-authoring` | Agent Skills   | agentskills.io 準拠で SKILL.md・description・progressive disclosure・評価ループを設計・レビューする   |
| `conventional-commit`   | Git / Workflow | Conventional Commits と Gitmoji を前提に、staged changes を適切に分割して commit message を組み立てる |
| `github-project-ops`    | GitHub / Ops   | GitHub Projects、Issues、sub-issues、merge queue を使った Issue 駆動開発の運用を設計・実行する        |

## Notes

- 公開時は git tag を切って pin できる状態にする
- skill を増やす場合も `<skill-name>/` を root 直下に置く
- README の表に用途を足して分類する

## License

MIT
