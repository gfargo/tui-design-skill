# TypeScript / JavaScript ecosystem — Ink, Clack, Inquirer

The Node.js ecosystem splits along two axes:
- **Pretty CLI** (argparse + color + prompts/spinners) vs **full TUI**.
- **Imperative/retained-mode** vs **declarative/React-style**.

**Ink has effectively won the high-end TUI space.** It powers Claude Code, GitHub Copilot CLI, Gemini CLI, Cloudflare Wrangler, Gatsby CLI, Prisma, Shopify CLI, Linear's internal CLI, Canva CLI, and tap. Anthropic's Claude Code is publicly TypeScript + React + Ink + Yoga + Bun.

## Quick recommendation

| If the user wants… | Use |
|---|---|
| Full-screen TUI app | **Ink** (React-flexbox) |
| Modern Clack-style wizard prompts | **@clack/prompts** |
| Prompt-heavy CLI (many questions) | **@inquirer/prompts** (Inquirer v9+) |
| Single elegant spinner | **ora** |
| Hierarchical task runner | **listr2** |
| Argparse, simple | **commander** (de facto default) |
| Argparse, validation-heavy | **yargs** |
| Heroku-class plugin CLI | **oclif** (Salesforce's framework) |
| Argparse, TS-first, lightweight | **citty** (UnJS) |
| Tiny argparse | **cac** (~7K) or `node:util.parseArgs` |
| Terminal colors, performance-critical | **picocolors** |
| Terminal colors, classic API | **chalk** |
| Single boxed message | **boxen** |
| Beyond Ink's perf ceiling | **OpenTUI** (Zig-backed, v0.x) |
| Image rendering in terminal | **terminal-kit** |

**Default modern stack:**
- One-shot interactive setup: **commander + @clack/prompts + picocolors**.
- Full TUI app: **Ink + @inkjs/ui + zustand + commander + ink-testing-library**.
- Heavy CLI with many subcommands: **oclif** or **commander + @inquirer/prompts + listr2**.

---

## Ink (vadimdemedes/ink)

**Architectural model: React for the terminal.** A custom `react-reconciler` renderer that commits to terminal-native host nodes (`ink-root`, `ink-box`, `ink-text`), runs Yoga layout, paints into a screen buffer, diffs against the previous frame, and emits ANSI patches in a single buffered terminal write.

**Hello world:**

```tsx
import React, {useState} from 'react';
import {render, Text, Box, useInput, useApp} from 'ink';

const App = () => {
  const [n, setN] = useState(0);
  const {exit} = useApp();

  useInput((input, key) => {
    if (key.upArrow) setN(c => c + 1);
    if (key.downArrow) setN(c => c - 1);
    if (input === 'q') exit();
  });

  return (
    <Box borderStyle="round" padding={1}>
      <Text color="green">Counter: {n}</Text>
    </Box>
  );
};

render(<App />);
```

## Primitives

Ink ships only a handful of components — everything else composes from these:

- **`<Text>`** — only place strings can live. Props: `color`, `backgroundColor`, `bold`, `italic`, `underline`, `inverse`, `dimColor`, `wrap`, `strikethrough`. Strings as direct children of `<Box>` will throw — they must be wrapped.
- **`<Box>`** — flexbox container. Props: `padding`, `paddingX/Y/Top/Right/Bottom/Left`, `margin*`, `borderStyle`, `borderColor`, `borderTop`/`Bottom`/`Left`/`Right` (selective borders), `width`, `height`, `flexDirection`, `flexGrow`, `flexShrink`, `flexBasis`, `justifyContent`, `alignItems`, `gap`, `display: 'flex' | 'none'`.
- **`<Newline>`** — vertical spacing.
- **`<Spacer>`** — flex-grow filler in a flex layout.
- **`<Static>`** — renders items permanently above the live UI; once rendered, never re-renders. Used for log streaming (Jest, Listr2) so the live UI doesn't have to repaint thousands of historical log lines.
- **`<Transform>`** — wraps children and transforms their rendered string. Used for gradients, OSC 8 hyperlinks, custom effects.

## Layout

Yoga (Meta's open-source flexbox engine, same as React Native). No CSS, no className — props on `<Text>` and `<Box>`. Border styles come from `cli-boxes`: `single`, `double`, `round`, `bold`, `singleDouble`, `doubleSingle`, `classic`, plus custom char strings.

```tsx
<Box flexDirection="column" height="100%">
  <Box borderStyle="single">
    <Text>Header</Text>
  </Box>
  <Box flexGrow={1} flexDirection="row">
    <Box width={30} borderStyle="single">
      <Text>Sidebar</Text>
    </Box>
    <Box flexGrow={1} borderStyle="single">
      <Text>Main content</Text>
    </Box>
  </Box>
</Box>
```

## Hooks

Ink-specific:
- **`useInput((input, key) => ...)`** — keyboard events. `key` is `{upArrow, downArrow, leftArrow, rightArrow, return, escape, tab, ctrl, shift, meta, pageUp, pageDown}`.
- **`useApp()`** — `{exit, exitWithError}`.
- **`useStdin()`** — `{stdin, setRawMode, isRawModeSupported}`.
- **`useStdout()`** / **`useStderr()`** — write outside the live UI.
- **`useFocus({autoFocus, isActive, id})`** — Tab-focusable component.
- **`useFocusManager()`** — `{focus(id), focusNext, focusPrevious, enableFocus, disableFocus}`.
- **`useWindowSize()`** — `{columns, rows}`, updates on resize.

Plus all standard React hooks (`useState`, `useEffect`, `useReducer`, `useContext`, `useMemo`).

State management for larger apps: **Zustand** (recommended), **Jotai**, or just `useReducer` + Context.

## ink-ui (vadimdemedes/ink-ui)

The companion component library — themeable widgets you don't want to write yourself:

- `<TextInput>`, `<EmailInput>`, `<PasswordInput>` — input fields with controlled state.
- `<Select>`, `<MultiSelect>` — choose from options.
- `<ConfirmInput>` — y/n prompt.
- `<Spinner>` — animated spinner (use this inside Ink, not `ora`).
- `<ProgressBar>` — determinate progress.
- `<Badge>` — colored status pill.
- `<StatusMessage>` — `success`/`info`/`warning`/`error` variants.
- `<Alert>` — bordered alert box.

Theming via theme objects passed at the root.

## Testing — ink-testing-library

```tsx
import {render} from 'ink-testing-library';

const {lastFrame, rerender, stdin, frames, unmount} = render(<App />);
expect(lastFrame()).toBe('Counter: 0');
stdin.write('\u001B[A');  // up arrow
expect(lastFrame()).toBe('Counter: 1');
```

Plus `renderToString()` (Ink 6.8+) for synchronous render-to-string in tests.

## Pastel — Next.js-style filesystem routing

`vadimdemedes/pastel` builds CLI command structure from filesystem layout, with Zod schemas for argument validation. Like Next.js for CLIs:

```
commands/
  index.tsx        // "myapp"
  create.tsx       // "myapp create"
  list.tsx         // "myapp list"
  user/
    add.tsx        // "myapp user add"
    remove.tsx     // "myapp user remove"
```

Each file exports a default React component plus optional `args`/`options` Zod schemas.

## Strengths and weaknesses

**Strengths:**
- Declarative, full React ecosystem available (use any state library, any hooks).
- Yoga flexbox is genuinely good for terminal layout.
- Excellent testing story.
- React Devtools work (`DEV=true` env var).
- Used by some of the most-deployed CLIs in the world.

**Weaknesses:**
- **Heavy startup**: React + Yoga + reconciler ≈ 80–150ms cold start. Bad for one-shot scripts where users expect instant response. For frequently-invoked commands (`mycli --version`, `mycli completion`), provide a fast path that bypasses Ink.
- **ESM-only since Ink 5.** For CJS, pin Ink 4 or use a bundler.
- **High-frequency re-renders flicker.** When streaming LLM tokens or tailing logs, use `useDeferredValue` or manual debounce. `<Static>` exists specifically to handle large append-only logs without re-rendering them.
- **Screen-reader support is rudimentary** (`INK_SCREEN_READER=true` enables a subset).

## Pitfalls

1. **Strings as direct children of `<Box>` throw.** Wrap in `<Text>`.
2. **Raw mode requires TTY.** Guard with `if (process.stdin.isTTY)`.
3. **`nodemon` breaks Inquirer/Ink arrow keys.** Use `nodemon --no-stdin` or `node --watch`.
4. **`ora` and Ink fight over the terminal.** Use `<Spinner>` from `@inkjs/ui` instead inside Ink.
5. **Don't run Ink and `blessed` in the same command** — both grab raw mode and alt-screen.
6. **`console.log` from Ink 3+ is intercepted** and displayed cleanly above the live UI. Don't fight it.
7. **CI detection**: check `process.env.CI` and degrade to non-interactive output.
8. **Older Windows cmd.exe** doesn't support all ANSI; target Windows Terminal.

---

## Modern prompts: @clack/prompts

`@clack/prompts` (~4 KB gzipped) has largely displaced Inquirer for new wizard-style CLIs. Used by **create-vite, create-astro, create-svelte, create-t3-app**, and inspired the Rust port `cliclack`.

```ts
import {intro, outro, text, confirm, select, spinner, isCancel, cancel} from '@clack/prompts';

intro('create-my-app');

const name = await text({
  message: 'Project name',
  validate: v => v.length === 0 ? 'Required' : undefined,
});
if (isCancel(name)) {
  cancel('Cancelled');
  process.exit(0);
}

const framework = await select({
  message: 'Pick a framework',
  options: [
    {value: 'react', label: 'React'},
    {value: 'vue', label: 'Vue'},
    {value: 'svelte', label: 'Svelte'},
  ],
});

const s = spinner();
s.start('Installing dependencies');
await install();
s.stop('Dependencies installed');

outro(`You're all set!`);
```

**Components:** `intro`/`outro`, `text`, `password`, `confirm`, `select`, `multiselect`, `groupMultiselect`, `selectKey`, `spinner`, `progress`, `taskLog`, `note`, `log.info/.warn/.error/.success`, `stream`, `group`.

**`isCancel(value)`** is critical — it detects Ctrl+C per prompt and lets you clean up gracefully.

The visual style — blue-bordered connectors between prompts, single Unicode glyph progress markers — has become a recognizable aesthetic. If the user's building a `create-*`-style scaffolder, this is the right choice.

---

## @inquirer/prompts

Inquirer v9+ rewrite with modular packages and TypeScript types. The workhorse for prompt-heavy CLIs:

```ts
import {input, select, confirm, password} from '@inquirer/prompts';

const name = await input({message: 'What is your name?'});
const role = await select({
  message: 'Choose a role',
  choices: [
    {name: 'Admin', value: 'admin'},
    {name: 'User', value: 'user'},
  ],
});
```

**Modular packages:** `@inquirer/input`, `@inquirer/select`, `@inquirer/checkbox`, `@inquirer/confirm`, `@inquirer/password`, `@inquirer/editor`, `@inquirer/expand`, `@inquirer/rawlist`, `@inquirer/search`, `@inquirer/number`. Pull only what you use.

**i18n** via `@inquirer/i18n`.

**When to choose Inquirer over Clack:** complex prompt flows with conditional questions, validation chains, custom prompt types (extensible plugin architecture), i18n requirements. **When to choose Clack over Inquirer:** modern aesthetic, minimal API, you're scaffolding (a `create-*` tool).

---

## Color libraries

| Library | Size | Speed | API | Best for |
|---|---|---|---|---|
| **picocolors** | 7 KB | Fastest single-style | Functional only: `pc.red('hi')` | Tooling internals (PostCSS, SVGO, Stylelint, Browserslist, Babel, Prettier, Vite all use it) |
| **chalk** | 101 KB | Slower; chainable | `chalk.red.bold('hi')` | End-user CLIs with frequent chaining; truecolor; familiar |
| **kleur** | Small | Fast | Chainable | Middle ground |
| **ansis** | Small | Fastest when chaining 2+ | Chainable + truecolor | Performance-critical with chained styles |

**All modern libraries respect `NO_COLOR`** automatically. **chalk v5+ is ESM-only**; pin v4 for CJS or use a bundler.

Recommendation: **picocolors for libraries / internal tools, chalk for user-facing CLIs.**

---

## Other utilities

- **ora** — single elegant spinner; ~70+ styles via `cli-spinners`. Use outside Ink. Inside Ink, use `<Spinner>` from `@inkjs/ui`.
- **cli-progress** — single and multi-bar progress with ETA. Use outside Ink.
- **listr2** — hierarchical animated task list with concurrency, retries, rollback. Renderers: `default` (live), `simple` (line-per-task, CI-friendly), `verbose`, `silent`, `test`. ~36M weekly downloads.
- **boxen** — text in boxes; used by `update-notifier`. Useful for one-time announcements ("Update available!").
- **figlet** + **gradient-string** — banner text with color gradients, for branding splashes.
- **terminal-link** — OSC 8 hyperlinks; falls back to plain URL on terminals without support.
- **string-width** — cell width for strings (handles CJK, emoji). Ink uses it internally.
- **update-notifier** — checks npm registry for newer versions; shows a boxed notice.

---

## Argument parsers

| Parser | Weekly DL | Style | Best for |
|---|---|---|---|
| **commander** | ~500M | Fluent API | The default for most projects (webpack, babel, vue-cli) |
| **yargs** | High | Fluent + middleware | Best validation; used by Mocha, nyc, jest |
| **citty** | Growing | TS-first, declarative | UnJS ecosystem (Nuxt, Nitro, unbuild) |
| **cac** | Lower | Tiny ~7K | Vite uses it; minimal deps |
| **oclif** | Plugin marketplace | Class-per-command | Heroku, Salesforce, Shopify CLI; cold start ~85ms |
| **node:util.parseArgs** | stdlib | Argparse only | Stable since Node 18; zero-dep |

**Startup overhead** (cold start): no framework ≈12ms, commander ≈18ms, yargs ≈35ms, oclif ≈85ms. For frequently-invoked CLIs, this matters.

**commander hello world:**

```ts
import {Command} from 'commander';

const program = new Command();
program
  .name('myapp')
  .description('CLI to do things')
  .version('1.0.0');

program.command('greet')
  .description('Say hello')
  .option('-n, --name <name>', 'who to greet', 'world')
  .action(({name}) => console.log(`Hello, ${name}!`));

program.parse();
```

---

## OpenTUI (anomalyco/opentui)

The credible new entrant: TypeScript bindings over a Zig native core via C ABI. Double-buffered rendering with alpha blending, scissor clipping, hit grid for mouse. Three packages: `@opentui/core` (low-level), `@opentui/react` (React renderer), `@opentui/solid` (SolidJS renderer).

Powers **opencode** (sst's terminal coding agent) and **terminal.shop**.

**Choose if** pushing past Ink's performance ceiling — animations, real-time streaming with low latency, or complex layouts where Yoga's CPU cost matters. **Trade-off:** v0.x churn, smaller community than Ink, native binary in the install.

---

## blessed / neo-blessed / terminal-kit

Retained-mode classics, pre-Ink era.

- **blessed** — reimplements ncurses in pure JS with terminfo/termcap parsing, painter's algorithm with damage buffers. Massive widget set: `box`, `list`, `form`, `textbox`, `textarea`, `progressbar`, `log`, `table`, `tree`, `terminal` (embedded shell). **Largely abandoned** — last release 2017.
- **neo-blessed** — maintained fork of blessed.
- **terminal-kit** (~82K weekly DL) — cursor control, screen buffers, input fields, menus, **image rendering (truecolor + Sixel)**, even a Document model.

**Choose** for image rendering, precise damage-region control, or maintaining legacy code. **Don't choose** for new TUI apps in 2026 — Ink is better-supported and the React/JSX model is more productive.

---

## Notable JS/TS TUI apps to study

- **Claude Code** (Anthropic) — Ink + React.
- **GitHub Copilot CLI** — Ink.
- **Gemini CLI** — Ink.
- **Cloudflare Wrangler** — Ink.
- **Gatsby CLI** — Ink (was one of the first major adopters).
- **Prisma CLI** — Ink.
- **opencode** (sst) — OpenTUI.
- **terminal.shop** — OpenTUI; novel "shop in your terminal" use case.
- **create-vite, create-astro, create-svelte** — Clack-style scaffolders.
- **Listr** demos — task runner aesthetic.

---

## Pitfalls common to JS/TS terminal apps

1. **ESM/CJS**. Almost the entire modern stack (chalk v5+, ora v6+, ink v4+, @inquirer/prompts, @clack/prompts, picocolors) is ESM-only at latest. For CJS, pin older majors or bundle.
2. **Restore terminal state on exit.** Ink: `unmount()`. blessed: `screen.destroy()`. Listen on SIGINT/SIGTERM.
3. **Detect non-TTY and CI.** `process.stdout.isTTY === false` or `process.env.CI` — degrade to plain output. Spinners and prompts must not run in CI.
4. **Raw mode requires `process.stdin.isTTY`.** Pipe input fails silently otherwise. Guard.
5. **Cell width**. Use `string-width` (Ink does); never `.length` for terminal width math.
6. **Frequently-invoked CLI startup**. Lazy-load subcommand modules. Have a fast path for `--version`/`--help`.
7. **Don't mix raw-mode libraries.** Ink + ora, Ink + blessed → broken.
8. **Windows older `cmd.exe`** doesn't support all ANSI. Target Windows Terminal.

---

## Stack recommendations by project shape

**Simple non-interactive CLI** (~50ms cold start, ~30 KB deps):
```
commander + picocolors + ora
```

**Interactive setup wizard** (`create-*` tool):
```
@clack/prompts + picocolors + commander
```

**Complex CLI with tasks**:
```
commander + @inquirer/prompts + listr2 + chalk + boxen + update-notifier
```

**Full TUI app**:
```
ink + @inkjs/ui + zustand + commander + ink-testing-library
```

**Heroku-class plugin CLI**:
```
oclif + ink + chalk + listr2
```

**Performance-critical / animated TUI**:
```
@opentui/core or @opentui/react
```

---

## Idioms summary

- **Ink**: Strings only inside `<Text>`. Use Yoga flexbox properties on `<Box>`. Use ink-ui components rather than reinventing. Use `<Static>` for log streams. Use `useDeferredValue` for streaming text. Test with ink-testing-library.
- **Clack**: Always `isCancel`-check every prompt. Use `intro`/`outro` to frame the flow. Use `spinner` for async work, `taskLog` for streaming output.
- **Inquirer**: Use modular `@inquirer/*` imports, not the v8 `inquirer` package.
- **picocolors** for tooling, **chalk** for user CLIs.
- **commander** unless you have a reason to use something else.
- For SSH-served Node apps, use **ssh2** + a custom shell handler — Ink doesn't have a direct equivalent to Charm's Wish, but the pattern works.

For deeper patterns shared across apps, see `references/visual-patterns.md` and `references/interaction-patterns.md`.
