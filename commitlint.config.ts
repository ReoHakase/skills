import type { UserConfig } from "@commitlint/types";

const config: UserConfig = {
  extends: ["@commitlint/config-conventional"],
  parserPreset: {
    parserOpts: {
      headerPattern: /^(\w*)(?:\((.*)\))?!?:\s+\S+\s+(.*)$/,
      headerCorrespondence: ["type", "scope", "subject"],
      breakingHeaderPattern: /^(\w*)(?:\((.*)\))?!:\s+\S+\s+(.*)$/,
      issuePrefixes: ["#"],
      noteKeywords: ["BREAKING CHANGE"],
    },
  },
  rules: {
    "header-max-length": [2, "always", 100],
    "subject-case": [0],
  },
  helpUrl:
    "https://github.com/ReoHakase/skills/blob/main/conventional-commit/SKILL.md",
};

export default config;
