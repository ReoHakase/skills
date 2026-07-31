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
├── github-issue-pr-ops/
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
| `github-issue-pr-ops`   | GitHub / Ops   | Projectに依存せず、Issue分割、本文、作業権、branch、PR、レビューからマージまでの契約を設計・運用する  |
| `github-project-ops`    | GitHub / Ops   | GitHub Projectの項目、フィールド、ビュー、工数、容量、Forecast、実行Wave、導入・解除を設計・運用する  |

## Install / Update

例は Codex 向けです。ほかの agent に入れる場合は `codex` や
`targets.agents` を対象 agent の指定に置き換えてください。

| Method             | Use case                                   | State management                    |
| ------------------ | ------------------------------------------ | ----------------------------------- |
| `npx skills`       | 手元で素早く install / update する         | manifest なし                       |
| `apm`              | project ごとに再現可能に install する      | `apm.yml` と lockfile で管理        |
| `agent-skills-nix` | Nix / Home Manager で宣言的に install する | `flake.lock` で source revision pin |

### `npx skills`

https://github.com/vercel-labs/skills

```bash
npx skills add ReoHakase/skills --list
npx skills add ReoHakase/skills --skill agentskills-authoring -a codex -y
npx skills add ReoHakase/skills --skill github-issue-pr-ops -a codex -y
npx skills add ReoHakase/skills --skill '*' -a codex -y
npx skills update -p -y
npx skills update agentskills-authoring -p -y
```

user scope に入れる場合だけ `-g` を付けます。user scope の更新は
`npx skills update -g -y` です。

### `apm`

https://github.com/microsoft/apm

```bash
apm install ReoHakase/skills --target codex
apm install ReoHakase/skills/agentskills-authoring --target codex
apm install ReoHakase/skills/github-issue-pr-ops --target codex
apm deps update --target codex
apm update --check
apm update
```

`apm deps update` は installed skill dependencies を更新します。
`apm update` は APM CLI 自体の更新です。

### `agent-skills-nix`

https://github.com/Kyure-A/agent-skills-nix

```nix
inputs.reohakase-skills = {
  url = "github:ReoHakase/skills";
  flake = false;
};

programs.agent-skills = {
  enable = true;
  sources.reohakase = {
    input = "reohakase-skills";
    filter.maxDepth = 1;
  };
  skills.enable = [
    "agentskills-authoring"
    "conventional-commit"
    "github-issue-pr-ops"
    "github-project-ops"
  ];
  targets.agents.enable = true;
};
```

この repository は root 直下の `<skill-name>/SKILL.md` だけを skill として扱うため、
`filter.maxDepth = 1` を指定しています。

```bash
nix flake lock --update-input reohakase-skills
home-manager switch --flake .#<profile>
```

## Notes

- 公開時は git tag を切って pin できる状態にする
- skill を増やす場合も `<skill-name>/` を root 直下に置く
- README の表に用途を足して分類する

## License

MIT
