#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const readline = require("readline");

const ROOT = path.resolve(__dirname, "..");
const VERSION = "0.1.0";
const MANAGER = "company-agent-harness";
const MANAGED_BLOCK_START = "<!-- company-agent-harness:start -->";
const MANAGED_BLOCK_END = "<!-- company-agent-harness:end -->";
const DEFAULT_WORKFLOW = "superpowers";
const DEFAULT_ARCHITECTURE_SKILL = "springboot-kotlin-backend-architecture";
const DEFAULT_SESSION_ROOT = ".harness/sessions";
const DEFAULT_COMPOUND_ROOT = process.env.HARNESS_COMPOUND_ROOT || "${HARNESS_COMPOUND_ROOT}";
const SKILLS = ["feature-development-harness", "springboot-kotlin-backend-architecture"];
const AGENTS = ["codex", "claude", "gemini"];
const WORKFLOW_ENGINES = ["superpowers", "gstack", "ouroboros", "oh-my-codex", "oh-my-claudecode"];

function usage() {
  return `Usage:
  agent-harness install [--location global|project] [--project-root <path>] [--agents codex,claude-code,gemini]
  agent-harness project-setup [--compound-root <path>] [--project-root <path>] [--workflow <engine>]
  agent-harness update [--type skill|project|all] [--location global|project|both] [--agents codex,claude-code,gemini]
  agent-harness uninstall [--type skill|project|all] [--scope global|project|all] [--agents codex,claude,gemini]
  agent-harness doctor

Examples:
  npx github:moohee-lee/spring-kotlin-harness install
  npx github:moohee-lee/spring-kotlin-harness project-setup
  npx github:moohee-lee/spring-kotlin-harness update --type skill --location global --agents codex
  npx github:moohee-lee/spring-kotlin-harness uninstall --type all --scope all
`;
}

function parseArgs(argv) {
  const result = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      result._.push(token);
      continue;
    }
    const eq = token.indexOf("=");
    if (eq >= 0) {
      result[token.slice(2, eq)] = token.slice(eq + 1);
      continue;
    }
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      result[key] = true;
      continue;
    }
    result[key] = next;
    i += 1;
  }
  return result;
}

function splitList(value, fallback) {
  if (!value) return fallback;
  return String(value)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeAgentName(value) {
  const normalized = String(value).trim().toLowerCase().replace(/\s+/g, "-");
  if (normalized === "claude-code" || normalized === "claude") return "claude";
  if (normalized === "gemini-cli" || normalized === "gemini") return "gemini";
  if (normalized === "codex") return "codex";
  return normalized;
}

function normalizeAgents(value, fallback) {
  return splitList(value, fallback).map(normalizeAgentName);
}

function requireKnown(name, value, allowed) {
  if (!allowed.includes(value)) {
    throw new Error(`Invalid ${name}: ${value}. Expected one of: ${allowed.join(", ")}`);
  }
}

function mkdirp(target) {
  fs.mkdirSync(target, { recursive: true });
}

function readText(target) {
  return fs.readFileSync(target, "utf8");
}

function writeText(target, content) {
  mkdirp(path.dirname(target));
  fs.writeFileSync(target, content, "utf8");
}

function exists(target) {
  return fs.existsSync(target);
}

function removePath(target) {
  fs.rmSync(target, { recursive: true, force: true });
}

function copyDir(source, target) {
  mkdirp(target);
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    if (entry.name === "__pycache__" || entry.name === ".DS_Store" || entry.name === "tests") {
      continue;
    }
    const sourcePath = path.join(source, entry.name);
    const targetPath = path.join(target, entry.name);
    if (entry.isDirectory()) {
      copyDir(sourcePath, targetPath);
    } else if (entry.isFile()) {
      mkdirp(path.dirname(targetPath));
      fs.copyFileSync(sourcePath, targetPath);
    }
  }
}

function hashDir(dir) {
  const hash = crypto.createHash("sha256");
  function visit(current, base) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      if (entry.name === ".company-harness-managed.json" || entry.name === "__pycache__") continue;
      const currentPath = path.join(current, entry.name);
      const rel = path.join(base, entry.name);
      if (entry.isDirectory()) {
        visit(currentPath, rel);
      } else if (entry.isFile()) {
        hash.update(rel);
        hash.update(fs.readFileSync(currentPath));
      }
    }
  }
  visit(dir, "");
  return `sha256:${hash.digest("hex")}`;
}

function markerPath(target) {
  return path.join(target, ".company-harness-managed.json");
}

function isManaged(target) {
  const marker = markerPath(target);
  if (!exists(marker)) return false;
  try {
    return JSON.parse(readText(marker)).manager === MANAGER;
  } catch (_) {
    return false;
  }
}

function backupPath(target, home) {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  return path.join(home, ".company-agent-harness", "backups", stamp, path.basename(target));
}

function installSkill({ agent, scope, projectRoot, home, overwrite, adopt }) {
  const base = skillBaseDir(agent, scope, projectRoot, home);
  const outputs = [];
  ensureAgentScaffold(agent, scope, projectRoot, home);

  for (const skill of SKILLS) {
    const source = path.join(ROOT, "skills", skill);
    const target = path.join(base, skill);
    if (!exists(source)) throw new Error(`Missing bundled skill: ${source}`);

    if (exists(target) && !isManaged(target)) {
      if (adopt) {
        writeMarker(target, { agent, scope, skill, source, contentHash: hashDir(target) });
        outputs.push(`adopted ${target}`);
        continue;
      }
      if (!overwrite) {
        outputs.push(`conflict ${target}`);
        continue;
      }
      const backup = backupPath(target, home);
      mkdirp(path.dirname(backup));
      fs.renameSync(target, backup);
      outputs.push(`backed up ${target} -> ${backup}`);
    }

    if (exists(target)) removePath(target);
    copyDir(source, target);
    writeMarker(target, {
      agent,
      scope,
      skill,
      source,
      contentHash: hashDir(target),
    });
    outputs.push(`installed ${agent}:${scope}:${skill} -> ${target}`);
  }
  return outputs;
}

function uninstallSkill({ agent, scope, projectRoot, home }) {
  const base = skillBaseDir(agent, scope, projectRoot, home);
  const outputs = [];
  for (const skill of SKILLS) {
    const target = path.join(base, skill);
    if (!exists(target)) {
      outputs.push(`missing ${target}`);
      continue;
    }
    if (!isManaged(target)) {
      outputs.push(`skipped unmanaged ${target}`);
      continue;
    }
    removePath(target);
    outputs.push(`removed ${target}`);
  }
  cleanupAgentScaffold(agent, scope, projectRoot, home, outputs);
  return outputs;
}

function writeMarker(target, fields) {
  const marker = {
    manager: MANAGER,
    version: VERSION,
    installedAt: new Date().toISOString(),
    ...fields,
  };
  writeText(markerPath(target), `${JSON.stringify(marker, null, 2)}\n`);
}

function skillBaseDir(agent, scope, projectRoot, home) {
  if (scope === "global") {
    if (agent === "codex") return path.join(process.env.CODEX_HOME || path.join(home, ".codex"), "skills");
    if (agent === "claude") return path.join(home, ".claude", "skills");
    if (agent === "gemini") return path.join(home, ".gemini", "skills");
  }
  if (scope === "project") {
    if (agent === "codex") return path.join(projectRoot, ".agents", "skills");
    if (agent === "claude") return path.join(projectRoot, ".claude", "skills");
    if (agent === "gemini") return path.join(projectRoot, ".agents", "skills");
  }
  throw new Error(`Unsupported agent/scope: ${agent}/${scope}`);
}

function extensionRoot(agent, scope, projectRoot, home) {
  if (agent !== "gemini") return null;
  if (scope === "global") return path.join(home, ".gemini", "extensions", MANAGER);
  return path.join(projectRoot, ".gemini", "extensions", MANAGER);
}

function ensureAgentScaffold(agent, scope, projectRoot, home) {
  if (agent !== "gemini") return;
  const root = extensionRoot(agent, scope, projectRoot, home);
  if (!root) return;
  mkdirp(root);
}

function cleanupAgentScaffold(agent, scope, projectRoot, home, outputs) {
  void agent;
  void scope;
  void projectRoot;
  void home;
  void outputs;
}

function configYaml({ workflow, architectureSkill, compoundRoot }) {
  return `harness:
  workflow_engine: ${workflow}
  architecture_skill: ${architectureSkill}

  compound:
    root: ${compoundRoot}
    mode: shared
    write_policy: reusable_lessons_only

  session_summary:
    root: ${DEFAULT_SESSION_ROOT}
    scope: project_local
    store_raw_prompt: false
    store_raw_answer: false
    store_summary: true
`;
}

function projectInstructionBlock({ workflow, architectureSkill }) {
  return `${MANAGED_BLOCK_START}
Use $feature-development-harness for feature development in this project.

- Read \`.harness/config.yaml\` before implementation.
- Use \`${architectureSkill}\` as the primary Spring Boot Kotlin architecture policy.
- Configured workflow engine: \`${workflow}\`.
- Search the shared Compound repository before implementation.
- Keep prompt and answer summaries in \`.harness/sessions\`.
- Write only reusable cross-project lessons to the shared Compound repository.

Architecture policy has priority over workflow-engine suggestions.
${MANAGED_BLOCK_END}
`;
}

function instructionFileName(kind) {
  if (kind === "agents") return "AGENTS.md";
  if (kind === "claude") return "CLAUDE.md";
  if (kind === "gemini") return "GEMINI.md";
  return null;
}

function upsertManagedBlock(file, block) {
  if (!exists(file)) {
    writeText(file, `# Agent Instructions\n\n${block}`);
    return `created ${file}`;
  }
  const body = readText(file);
  const pattern = new RegExp(`${escapeRe(MANAGED_BLOCK_START)}[\\s\\S]*?${escapeRe(MANAGED_BLOCK_END)}\\n?`, "g");
  if (pattern.test(body)) {
    writeText(file, body.replace(pattern, block));
    return `updated ${file}`;
  }
  const separator = body.trim() ? "\n\n" : "";
  writeText(file, `${body.trimEnd()}${separator}${block}`);
  return `updated ${file}`;
}

function removeManagedBlock(file) {
  if (!exists(file)) return `missing ${file}`;
  const body = readText(file);
  const pattern = new RegExp(`\\n*${escapeRe(MANAGED_BLOCK_START)}[\\s\\S]*?${escapeRe(MANAGED_BLOCK_END)}\\n*`, "g");
  const next = `${body.replace(pattern, "\n").trim()}\n`;
  if (next.trim() === "# Agent Instructions") {
    fs.unlinkSync(file);
    return `removed ${file}`;
  }
  writeText(file, next);
  return `updated ${file}`;
}

function escapeRe(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function setupProject({ projectRoot, workflow, architectureSkill, compoundRoot, instructions, force }) {
  const outputs = [];
  const harnessDir = path.join(projectRoot, ".harness");
  const sessions = path.join(projectRoot, DEFAULT_SESSION_ROOT);
  mkdirp(sessions);
  writeText(path.join(sessions, ".gitkeep"), "");

  const config = path.join(harnessDir, "config.yaml");
  const configExists = exists(config);
  if (!configExists || force) {
    writeText(config, configYaml({ workflow, architectureSkill, compoundRoot }));
    outputs.push(`${configExists ? "updated" : "created"} ${config}`);
  } else {
    outputs.push(`exists ${config}`);
  }

  writeText(path.join(harnessDir, ".company-harness-managed.json"), `${JSON.stringify({
    manager: MANAGER,
    scope: "project",
    version: VERSION,
    workflowEngine: workflow,
    architectureSkill,
    compoundRoot,
  }, null, 2)}\n`);
  outputs.push(`created ${path.join(harnessDir, ".company-harness-managed.json")}`);

  const instructionFile = instructionFileName(instructions);
  if (instructionFile) {
    outputs.push(upsertManagedBlock(
      path.join(projectRoot, instructionFile),
      projectInstructionBlock({ workflow, architectureSkill }),
    ));
  }
  outputs.push("project harness setup complete");
  return outputs;
}

function uninstallProject({ projectRoot, deleteSessions }) {
  const outputs = [];
  for (const filename of ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]) {
    const file = path.join(projectRoot, filename);
    if (exists(file) && readText(file).includes(MANAGED_BLOCK_START)) {
      outputs.push(removeManagedBlock(file));
    }
  }
  for (const file of [
    path.join(projectRoot, ".harness", "config.yaml"),
    path.join(projectRoot, ".harness", ".company-harness-managed.json"),
  ]) {
    if (exists(file)) {
      fs.unlinkSync(file);
      outputs.push(`removed ${file}`);
    }
  }
  if (deleteSessions) {
    const sessions = path.join(projectRoot, DEFAULT_SESSION_ROOT);
    if (exists(sessions)) {
      removePath(sessions);
      outputs.push(`removed ${sessions}`);
    }
  }
  const harnessDir = path.join(projectRoot, ".harness");
  if (exists(harnessDir) && fs.readdirSync(harnessDir).length === 0) {
    fs.rmdirSync(harnessDir);
    outputs.push(`removed ${harnessDir}`);
  }
  outputs.push("project harness uninstall complete");
  return outputs;
}

async function ask(question, choices, fallback) {
  const suffix = choices ? ` (${choices.join("/")})` : "";
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const answer = await new Promise((resolve) => rl.question(`${question}${suffix} [${fallback}]: `, resolve));
  rl.close();
  return answer.trim() || fallback;
}

async function askWithDescription({ title, description, choices, fallback }) {
  if (description) console.log(`\n${description}\n`);
  return ask(title, choices, fallback);
}

async function askMultiSelect({ title, description, choices, fallback }) {
  if (description) console.log(`\n${description}\n`);
  console.log(title);
  choices.forEach((choice, index) => {
    console.log(`  ${index + 1}. ${choice.label} (${choice.value})`);
    console.log(`     ${choice.description}`);
  });
  const fallbackText = fallback.join(",");
  const answer = await ask("Enter comma-separated numbers or names", null, fallbackText);
  const tokens = answer.split(",").map((item) => item.trim()).filter(Boolean);
  const values = tokens.map((token) => {
    const index = Number(token);
    if (Number.isInteger(index) && index >= 1 && index <= choices.length) {
      return choices[index - 1].value;
    }
    return token;
  });
  return values.join(",");
}

async function interactiveSetupDefaults(flags) {
  if (flags.yes || !process.stdin.isTTY) return flags;
  if (!flags.type) flags.type = await ask("Setup type", ["skill", "project", "both"], "project");
  if (!flags.scope && flags.type !== "project") flags.scope = await ask("Skill setup scope", ["global", "project", "both"], "global");
  if (!flags.agents && flags.type !== "project") flags.agents = await ask("Agents", ["codex", "claude", "gemini"], "codex");
  if (!flags.workflow) flags.workflow = await ask("Workflow engine", null, DEFAULT_WORKFLOW);
  return flags;
}

async function interactiveInstallDefaults(flags) {
  if (flags.yes || !process.stdin.isTTY) return flags;
  if (!flags.location && !flags.scope) {
    flags.location = await askWithDescription({
      title: "Installation location",
      choices: ["global", "project"],
      fallback: "project",
      description: [
        "Choose where the AI agent skills will be installed.",
        "- global: installs once for your user account and can be used from many projects.",
        "- project: installs into one repository so the setup can be committed and shared with that project.",
      ].join("\n"),
    });
  }
  if ((flags.location || flags.scope) === "project" && !flags["project-root"]) {
    flags["project-root"] = await askWithDescription({
      title: "Project installation directory",
      choices: null,
      fallback: process.cwd(),
      description: "Project location is the repository that should receive local skill files. Press Enter to use the current directory.",
    });
  }
  if (!flags.agents) {
    flags.agents = await askMultiSelect({
      title: "Choose AI agents to support",
      fallback: ["codex"],
      choices: [
        { value: "codex", label: "Codex", description: "Global: ~/.codex/skills, project: .agents/skills" },
        { value: "claude-code", label: "Claude Code", description: "Global: ~/.claude/skills, project: .claude/skills" },
        { value: "gemini", label: "Gemini CLI", description: "Global: ~/.gemini/skills, project: .agents/skills" },
      ],
      description: "Select every AI coding agent that should discover this harness. Multiple values are allowed.",
    });
  }
  return flags;
}

async function interactiveProjectSetupDefaults(flags) {
  if (flags.yes || !process.stdin.isTTY) return flags;
  if (!flags["compound-root"]) {
    flags["compound-root"] = await askWithDescription({
      title: "Compound repository path",
      choices: null,
      fallback: process.env.HARNESS_COMPOUND_ROOT || "",
      description: [
        "Enter the local path to the shared Compound repository clone.",
        "This must be an existing git clone. Project prompt and answer summaries stay local; reusable lessons go to this Compound repo.",
      ].join("\n"),
    });
  }
  if (!flags["project-root"]) {
    flags["project-root"] = await askWithDescription({
      title: "Project directory",
      choices: null,
      fallback: process.cwd(),
      description: "Enter the project repository that should receive .harness/config.yaml and the managed instruction block. Press Enter to use the current directory.",
    });
  }
  if (!flags.workflow && !flags["workflow-engine"]) {
    flags.workflow = await askWithDescription({
      title: "Workflow engine",
      choices: WORKFLOW_ENGINES,
      fallback: DEFAULT_WORKFLOW,
      description: [
        "Choose the process framework agents should use inside this project.",
        "The Spring Boot Kotlin architecture skill still has priority over the workflow engine.",
      ].join("\n"),
    });
  }
  return flags;
}

function setupSkillForScopes({ scopes, agents, projectRoot, home, overwrite, adopt }) {
  const outputs = [];
  for (const scope of scopes) {
    requireKnown("scope", scope, ["global", "project"]);
    for (const agent of agents) {
      requireKnown("agent", agent, AGENTS);
      outputs.push(...installSkill({ agent, scope, projectRoot, home, overwrite, adopt }));
    }
  }
  outputs.push("skill setup complete");
  return outputs;
}

function installSkillForLocation({ location, agents, projectRoot, home, overwrite, adopt, completionLabel = "skill install complete" }) {
  requireKnown("location", location, ["global", "project"]);
  const outputs = [];
  for (const agent of agents) {
    requireKnown("agent", agent, AGENTS);
    outputs.push(...installSkill({
      agent,
      scope: location,
      projectRoot,
      home,
      overwrite,
      adopt,
    }));
  }
  outputs.push(completionLabel);
  return outputs;
}

function uninstallSkillForScopes({ scopes, agents, projectRoot, home }) {
  const outputs = [];
  for (const scope of scopes) {
    requireKnown("scope", scope, ["global", "project"]);
    for (const agent of agents) {
      requireKnown("agent", agent, AGENTS);
      outputs.push(...uninstallSkill({ agent, scope, projectRoot, home }));
    }
  }
  outputs.push("skill uninstall complete");
  return outputs;
}

function normalizeScopes(scopeValue) {
  if (scopeValue === "all" || scopeValue === "both") return ["global", "project"];
  return [scopeValue || "global"];
}

function normalizeLocation(flags, fallback = "project") {
  return flags.location || flags.scope || fallback;
}

function isGitClone(directory) {
  if (!exists(directory) || !fs.statSync(directory).isDirectory()) return false;
  const gitPath = path.join(directory, ".git");
  return exists(gitPath);
}

function resolveProjectRoot(flags) {
  return path.resolve(flags["project-root"] || process.cwd());
}

function resolveWorkflow(flags) {
  const workflow = flags.workflow || flags["workflow-engine"] || DEFAULT_WORKFLOW;
  requireKnown("workflow", workflow, WORKFLOW_ENGINES);
  return workflow;
}

function installHelp() {
  return `agent-harness install

Install the harness skills into AI agent skill directories.

Options:
  --location global|project   Choose installation location. global means user-wide; project means one repository. Default: project
  --project-root <path>       Project install location when --location project is selected. Default: current directory
  --agents <list>             Comma-separated agents: codex, claude-code, gemini
  --yes                       Skip prompts and use defaults

Agent paths:
  codex       global ~/.codex/skills      project .agents/skills
  claude-code global ~/.claude/skills     project .claude/skills
  gemini      global ~/.gemini/skills     project .agents/skills
`;
}

function projectSetupHelp() {
  return `agent-harness project-setup

Apply harness configuration to a target project. This does not install agent skills.

Options:
  --compound-root <path>      Existing git clone of the shared Compound repository
  --project-root <path>       Target project directory. Default: current directory
  --workflow <engine>         One of: ${WORKFLOW_ENGINES.join(", ")}
  --instructions <kind>       agents, claude, gemini, or none. Default: agents
  --yes                       Skip prompts
`;
}

function updateHelp() {
  return `agent-harness update

Refresh managed skill installs and/or project harness config from this package.

Options:
  --type skill|project|all    What to update. Default: skill
  --location global|project|both
  --agents <list>             Comma-separated agents: codex, claude-code, gemini
  --project-root <path>       Project directory for project updates
  --compound-root <path>      Existing Compound repository path for project updates
`;
}

async function commandInstall(flags) {
  if (flags.help || flags.h) {
    console.log(installHelp());
    return;
  }
  flags = await interactiveInstallDefaults(flags);
  const location = normalizeLocation(flags, "project");
  requireKnown("location", location, ["global", "project"]);
  const projectRoot = resolveProjectRoot(flags);
  const home = path.resolve(flags.home || os.homedir());
  const agents = normalizeAgents(flags.agents, ["codex"]);
  const outputs = installSkillForLocation({
    location,
    agents,
    projectRoot,
    home,
    overwrite: Boolean(flags.overwrite),
    adopt: Boolean(flags.adopt),
  });
  console.log(outputs.join("\n"));
}

async function commandProjectSetup(flags) {
  if (flags.help || flags.h) {
    console.log(projectSetupHelp());
    return;
  }
  flags = await interactiveProjectSetupDefaults(flags);
  const projectRoot = resolveProjectRoot(flags);
  const compoundRoot = path.resolve(flags["compound-root"] || DEFAULT_COMPOUND_ROOT);
  if (!isGitClone(compoundRoot)) {
    throw new Error(`Compound repository path must be a git clone: ${compoundRoot}`);
  }
  const workflow = resolveWorkflow(flags);
  const outputs = setupProject({
    projectRoot,
    workflow,
    architectureSkill: flags["architecture-skill"] || DEFAULT_ARCHITECTURE_SKILL,
    compoundRoot,
    instructions: flags.instructions || "agents",
    force: Boolean(flags.force),
  });
  console.log(outputs.join("\n"));
}

async function commandUpdate(flags) {
  if (flags.help || flags.h) {
    console.log(updateHelp());
    return;
  }
  const type = flags.type || "skill";
  requireKnown("type", type, ["skill", "project", "all"]);
  const projectRoot = resolveProjectRoot(flags);
  const home = path.resolve(flags.home || os.homedir());
  const agents = normalizeAgents(flags.agents, ["codex"]);
  const outputs = [];

  if (type === "skill" || type === "all") {
    const locations = normalizeLocation(flags, "global") === "both"
      ? ["global", "project"]
      : [normalizeLocation(flags, "global")];
    for (const location of locations) {
      outputs.push(...installSkillForLocation({
        location,
        agents,
        projectRoot,
        home,
        overwrite: true,
        adopt: false,
        completionLabel: "skill update complete",
      }));
    }
  }

  if (type === "project" || type === "all") {
    const compoundRoot = path.resolve(flags["compound-root"] || DEFAULT_COMPOUND_ROOT);
    if (!isGitClone(compoundRoot)) {
      throw new Error(`Compound repository path must be a git clone: ${compoundRoot}`);
    }
    outputs.push(...setupProject({
      projectRoot,
      workflow: resolveWorkflow(flags),
      architectureSkill: flags["architecture-skill"] || DEFAULT_ARCHITECTURE_SKILL,
      compoundRoot,
      instructions: flags.instructions || "agents",
      force: true,
    }));
    outputs.push("project harness update complete");
  }

  console.log(outputs.join("\n"));
}

async function commandSetup(flags) {
  flags = await interactiveSetupDefaults(flags);
  const type = flags.type || "project";
  requireKnown("type", type, ["skill", "project", "both"]);
  const projectRoot = path.resolve(flags["project-root"] || process.cwd());
  const home = path.resolve(flags.home || os.homedir());
  const workflow = flags.workflow || flags["workflow-engine"] || DEFAULT_WORKFLOW;
  const architectureSkill = flags["architecture-skill"] || DEFAULT_ARCHITECTURE_SKILL;
  const compoundRoot = flags["compound-root"] || DEFAULT_COMPOUND_ROOT;
  const instructions = flags.instructions || "agents";
  const agents = normalizeAgents(flags.agents, ["codex"]);
  const scopes = normalizeScopes(flags.scope || (type === "both" ? "global" : "global"));
  const outputs = [];

  if (type === "skill" || type === "both") {
    outputs.push(...setupSkillForScopes({
      scopes,
      agents,
      projectRoot,
      home,
      overwrite: Boolean(flags.overwrite),
      adopt: Boolean(flags.adopt),
    }));
  }
  if (type === "project" || type === "both") {
    outputs.push(...setupProject({
      projectRoot,
      workflow,
      architectureSkill,
      compoundRoot,
      instructions,
      force: Boolean(flags.force),
    }));
  }
  console.log(outputs.join("\n"));
}

async function commandUninstall(flags) {
  const type = flags.type || "all";
  requireKnown("type", type, ["skill", "project", "all"]);
  const projectRoot = path.resolve(flags["project-root"] || process.cwd());
  const home = path.resolve(flags.home || os.homedir());
  const agents = normalizeAgents(flags.agents, AGENTS);
  const scopes = normalizeScopes(flags.scope || flags.location || "all");
  const outputs = [];

  if (type === "skill" || type === "all") {
    outputs.push(...uninstallSkillForScopes({ scopes, agents, projectRoot, home }));
  }
  if (type === "project" || type === "all") {
    outputs.push(...uninstallProject({ projectRoot, deleteSessions: Boolean(flags["delete-sessions"]) }));
  }
  console.log(outputs.join("\n"));
}

function commandDoctor() {
  const rows = [
    ["root", ROOT],
    ["node", process.version],
    ["feature skill", exists(path.join(ROOT, "skills", "feature-development-harness", "SKILL.md")) ? "present" : "missing"],
    ["architecture skill", exists(path.join(ROOT, "skills", DEFAULT_ARCHITECTURE_SKILL, "SKILL.md")) ? "present" : "missing"],
  ];
  console.log(rows.map(([key, value]) => `${key}: ${value}`).join("\n"));
}

async function main() {
  const [command, ...rest] = process.argv.slice(2);
  const flags = parseArgs(rest);
  if (!command || command === "--help" || command === "-h") {
    console.log(usage());
    return;
  }
  if (command === "install") {
    await commandInstall(flags);
    return;
  }
  if (command === "project-setup") {
    await commandProjectSetup(flags);
    return;
  }
  if (command === "update") {
    await commandUpdate(flags);
    return;
  }
  if (command === "setup") {
    await commandSetup(flags);
    return;
  }
  if (command === "uninstall") {
    await commandUninstall(flags);
    return;
  }
  if (command === "doctor") {
    commandDoctor();
    return;
  }
  throw new Error(`Unknown command: ${command}\n${usage()}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
