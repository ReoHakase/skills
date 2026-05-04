# agent-skills

APM で個別導入しやすいように、skill を root 直下に並べる公開用リポジトリです。

方針は固定です。

- skill は `<skill-name>/SKILL.md`
- `skills/` のような中間ディレクトリは作らない
- 分類は README の表と命名で扱う

## Repository Layout

```txt
agent-skills/
├── apm.yml
├── apm.lock.yaml
├── README.md
├── conventional-commit/
│   └── SKILL.md
├── package.json
├── lefthook.yml
└── commitlint.config.ts
```

## Skills

| Skill | Area | Use case |
|---|---|---|
| `conventional-commit` | Git / Workflow | Conventional Commits と Gitmoji を前提に、staged changes を適切に分割して commit message を組み立てる |

## Install

### `conventional-commit`

```bash
apm install ReoHakase/skills/conventional-commit
```

バージョンを固定する場合:

```bash
apm install ReoHakase/skills/conventional-commit#v0.1.0
```

グローバル導入:

```bash
apm install -g ReoHakase/skills/conventional-commit
```

利用者側の `apm.yml` 例:

```yaml
name: my-project
version: 1.0.0
dependencies:
  apm:
    - ReoHakase/skills/conventional-commit#v0.1.0
```

## Notes

- 公開時は git tag を切って `#v0.1.0` のように pin できる状態にする
- skill を増やす場合も `<skill-name>/` を root 直下に置く
- README の表に用途を足して分類する
