# TypeScript / JavaScript ecosystem — Ink, Clack, Inquirer

The Node.js ecosystem splits along two axes:
- **Pretty CLI** (argument parsing + color + prompts/spinners) vs **full TUI**.
- **Imperative/retained-mode** vs **declarative/React-style**.

**Ink has effectively won the high-end TUI space.** It powers Claude Code (publicly TypeScript + React + Ink + Yoga + Bun), GitHub Copilot CLI, Gemini CLI, and Cloudflare Wrangler.

**Contents:**
- [Quick recommendation](#quick-recommendation) · [Runtime floors and ESM](#runtime-floors-and-esm)
- [Ink](#ink-vadimdemedesink) — [Lifecycle and terminal handoff](#lifecycle-and-terminal-handoff) · [Primitives](#primitives) · [Layout](#layout) · [Hooks](#hooks) · [ink-ui](#ink-ui-vadimdemedesink-ui) · [Testing](#testing--ink-testing-library) · [Debugging](#debugging) · [Pastel](#pastel--nextjs-style-filesystem-routing) · [Strengths and weaknesses](#strengths-and-weaknesses) · [Ink pitfalls](#ink-pitfalls)
- [Modern prompts: @clack/prompts](#modern-prompts-clackprompts) · [@inquirer/prompts](#inquirerprompts)
- [Color libraries](#color-libraries) · [Other utilities](#other-utilities) · [Argument parsers](#argument-parsers)
- [OpenTUI](#opentui-anomalycoopentui) · [blessed / terminal-kit](#blessed--terminal-kit)
- [Cross-library pitfalls](#cross-library-pitfalls)
- [Stack recommendations by project shape](#stack-recommendations-by-project-shape)

## Quick recommendation

| If the user wants… | Use |
|---|---|
| Full-screen TUI app | **Ink** (React-flexbox) |
| Modern Clack-style wizard prompts | **@clack/prompts** |
| Prompt-heavy CLI (many questions) | **@inquirer/prompts** (the modern modular rewrite) |
| Single elegant spinner | **ora** |
| Hierarchical task runner | **listr2** |
| Argument parsing, simple | **commander** (de facto default) |
| Argument parsing, validation-heavy | **yargs** |
| Heroku-class plugin CLI | **oclif** (Salesforce's framework) |
| Argument parsing, TS-first, lightweight | **citty** (UnJS) |
| Tiny argument parser | **cac** (one ~20 KB file, no deps) or `node:util.parseArgs` |
| Terminal colors, performance-critical | **picocolors** |
| Terminal colors, classic API | **chalk** |
| Single boxed message | **boxen** |
| Beyond Ink's perf ceiling | **OpenTUI** (Zig-backed, v0.x) |
| Image rendering in terminal | **terminal-image** 5 (Kitty/iTerm2 protocols, half-block fallback) |

**Default full-TUI stack: Ink + @inkjs/ui + zustand + commander + ink-testing-library** (the last two UI/test packages are unmaintained but work with Ink 8; see ink-ui and Testing). For other project shapes, see "Stack recommendations by project shape" at the end.

## Runtime floors and ESM

Node 20 is end-of-life; target Node 22 or Node 24 (check the Node release schedule for LTS status). The current majors below need Node 22; use the last Node 20 line only as a bridge for a deployment that can't move yet.

| Package | Current major needs | Last line for Node 20 |
|---|---|---|
| Ink | Ink 7 and 8 require Node ≥ 22; Ink 8 also requires React ≥ 19.3 (Ink 7: ≥ 19.2) | Ink 6 (Node ≥ 20, React ≥ 19) |
| chalk | chalk 6 requires Node ≥ 22 | chalk 5 |
| commander | v15 is ESM-only and needs Node ≥ 22.12 | v14 (security fixes until May 2027) |
| listr2, execa | listr2 11 requires Node ≥ 22.13; execa 10 requires Node ≥ 22 | previous major |

Much of the modern stack (chalk v5+, ora v6+, ink v4+, commander v15+, @inquirer/prompts, @clack/prompts) is ESM-only at latest. On Node 20.19+/22.12+, CommonJS code can `require()` synchronous ESM packages such as chalk (`require('chalk').default`), commander, @clack/prompts, and @inquirer/prompts, so don't pin old CJS majors. Ink is the exception: Yoga's top-level await makes `require('ink')` throw `ERR_REQUIRE_ASYNC_MODULE` (Ink 6.8–8), so from CommonJS use `await import('ink')` or a bundler.

---

## Ink (vadimdemedes/ink)

**Architectural model: React for the terminal.** A custom `react-reconciler` renderer that commits to terminal-native host nodes (`ink-root`, `ink-box`, `ink-text`), runs Yoga layout, paints into a screen buffer, and rewrites the live output in a single buffered terminal write. By default each frame replaces the whole live region; `incrementalRendering: true` updates only the changed lines ([readme](https://github.com/vadimdemedes/ink/blob/v8.0.0/readme.md#incrementalrendering)).

Current major: **Ink 8** (8.0.x, October 2026); runtime floors are in the table above.

**Hello world:**

```tsx check=typescript/ink-hello
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

### Lifecycle and terminal handoff

Ink 7.1+ (unchanged in 8.0) distinguishes permanent React-tree unmounting from a resumable terminal suspension (`suspendTerminal` is not in 7.0 or Ink 6). Keep process-level signal policy at the render boundary and temporary ownership changes inside `useApp()`.

| Boundary | Ink 7.1+ contract |
|---|---|
| Normal exit | Use `useApp().exit(...)` inside the tree or the render handle's `unmount()` outside it. At the top level, await `waitUntilExit()` before post-run output or process termination so pending terminal writes finish. |
| SIGINT / SIGTERM | `exitOnCtrlC` handles Ctrl+C bytes while stdin is raw; it is not an operating-system SIGTERM handler. If the host requires graceful signals, register them once at the process boundary, unmount, await `waitUntilExit()`, set the intended exit status, and remove listeners. Do not call `process.exit()` before cleanup flushes. |
| Interactive child | Use `await suspendTerminal(async () => runChild())`. Ink pauses input and rendering, restores cursor/input/screen modes, runs the callback even without an interactive TTY, and re-enters with a full redraw in `finally`. Reload child-mutated data afterward because redraw preserves the existing React state. For the manual form, always `await suspension.resume()` in `finally` or use `await using`. Do not unmount. |
| Foreground suspend | Ink has no separate high-level job-control action. If a Unix-only Ctrl+Z feature is necessary, perform SIGTSTP inside `suspendTerminal` and let its resume path re-enter and redraw; expose a different action on Windows. |

The tagged [`suspendTerminal` documentation](https://github.com/vadimdemedes/ink/blob/v8.0.0/readme.md#suspendterminalcallback) includes callback, manual, non-interactive, and nesting behavior. A second overlapping suspension is an error, so centralize ownership rather than letting arbitrary components suspend independently.

### Primitives

Ink ships only a handful of components — everything else composes from these:

- **`<Text>`** — only place strings can live. Props: `color`, `backgroundColor`, `bold`, `italic`, `underline`, `inverse`, `dimColor`, `wrap`, `strikethrough`. Strings as direct children of `<Box>` will throw — they must be wrapped.
- **`<Box>`** — flexbox container. Props: `padding`, `paddingX/Y/Top/Right/Bottom/Left`, `margin*`, `borderStyle`, `borderColor`, `borderTop`/`Bottom`/`Left`/`Right` (selective borders), `width`, `height`, `minWidth`/`maxWidth` (numbers only in Ink 8), `flexDirection`, `flexGrow`, `flexShrink`, `flexBasis`, `justifyContent`, `alignItems`, `gap`, `display: 'flex' | 'none'`, `overflow`/`overflowX`/`overflowY`. Ink 8 adds `contentOffsetX`/`contentOffsetY` for scrolling: give a fixed-height viewport `overflow="hidden"`, wrap the content in a `flexShrink={0}` box that carries any padding, and clamp the offset to `content.height - clientHeight` from `useBoxMetrics()`.
- **`<Newline>`** — newline characters; only valid inside `<Text>`. Use `gap` or margin for vertical spacing between boxes.
- **`<Spacer>`** — flex-grow filler in a flex layout.
- **`<Static>`** — renders items permanently above the live UI; once rendered, never re-renders. Suited to log streaming, so the live UI doesn't repaint thousands of historical lines.
- **`<Transform>`** — wraps children and transforms their rendered string. Used for gradients, OSC 8 hyperlinks, custom effects.

### Layout

Yoga (Meta's open-source flexbox engine, same as React Native). No CSS, no className — props on `<Text>` and `<Box>`. Border styles come from `cli-boxes`: `single`, `double`, `round`, `bold`, `singleDouble`, `doubleSingle`, `classic`, or a custom `BoxStyle` object (`topLeft`, `top`, `topRight`, `left`, `right`, `bottomLeft`, `bottom`, `bottomRight`).

```tsx check=typescript/ink-layout
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

### Hooks

Ink-specific (items marked 7+ are not in Ink 6):
- **`useInput((input, key) => ...)`** — keyboard events. `key` is `{upArrow, downArrow, leftArrow, rightArrow, return, escape, tab, backspace, delete, ctrl, shift, meta, pageUp, pageDown, home, end}` (plus Kitty-protocol extras). Ink 8 drops mouse, focus, and cursor-position reports instead of passing them in as typed text, so mouse support must parse raw stdin.
- **`useApp()`** — `{exit(errorOrResult?), waitUntilRenderFlush (7+), suspendTerminal (7.1+)}`. Pass an `Error` to `exit` to reject the render handle's `waitUntilExit()`; there is no separate error variant. Use `suspendTerminal` for a resumable interactive child, not final shutdown.
- **`useStdin()`** — `{stdin, setRawMode, isRawModeSupported}`.
- **`useStdout()`** / **`useStderr()`** — write outside the live UI. Ink 8 types these streams as generic Node streams, so `stdout.columns` no longer type-checks; read the size from `useWindowSize()`.
- **`useFocus({autoFocus, isActive, id})`** — Tab-focusable component.
- **`useFocusManager()`** — `{focus(id), focusNext, focusPrevious, enableFocus, disableFocus, activeId (7+)}`.
- **`useWindowSize()`** (7+) — `{columns, rows}`, updates on resize.
- **`usePaste(callback)`** (7+) — bracketed-paste events, so pasted text arrives as one chunk instead of spraying through `useInput` character by character.
- **`useCursor()`** — position the real terminal cursor (IME-friendly input).
- **`useAnimation()`** (7+) — frame ticker; `isActive: false` stops it, and turning it back on resets the counters to 0 (it does not resume).
- **`useBoxMetrics()`** (7+) — measured dimensions of a box at runtime; Ink 8 adds `clientWidth`/`clientHeight`, the size inside its borders.

Plus all standard React hooks (`useState`, `useEffect`, `useReducer`, `useContext`, `useMemo`).

State management for larger apps: **Zustand** (recommended), **Jotai**, or just `useReducer` + Context.

### ink-ui (vadimdemedes/ink-ui)

The companion component library of themeable widgets:

- `<TextInput>`, `<EmailInput>`, `<PasswordInput>` — uncontrolled inputs: `defaultValue`, `onChange`, `onSubmit`, and no `value` prop (issue #20), so remount with a new `key` to clear one.
- `<Select>`, `<MultiSelect>`, `<ConfirmInput>` (y/n), `<ProgressBar>` (determinate), `<Badge>`, `<StatusMessage>` (`success`/`info`/`warning`/`error`), `<Alert>`.
- `<Spinner>` — animated spinner (use this inside Ink, not `ora`).

Theming via theme objects passed at the root. @inkjs/ui has had no release since 2.0.0 (May 2024) but works on Ink 8; fork or wrap any component you need to change.

### Testing — ink-testing-library

```tsx check=typescript/ink-testing-library
import {render} from 'ink-testing-library';

const tick = () => new Promise(resolve => setTimeout(resolve, 0));

const {lastFrame, rerender, stdin, frames, unmount} = render(<App />);
expect(lastFrame()).toContain('Counter: 0');  // frame includes the round border
stdin.write('\u001B[A');  // up arrow — see the input caveat below
await tick();             // input and re-render are asynchronous
expect(lastFrame()).toContain('Counter: 1');
unmount();
```

Plus `renderToString()` (Ink 6.8+) for synchronous render-to-string in tests.

**Staleness caveat.** ink-testing-library 4.0.0 was built against Ink 5 / React 18 (May 2024; unmaintained and still the latest release) but installs and works with Ink 6.8, 7.1, and 8. `stdin.write` drives `useInput` and `usePaste` as long as the test awaits after each write, because frames update asynchronously (the "stdin.write() does not trigger useInput" report reproduces only on Ink 5.0.1 when writing immediately after `render()`). Frames are text only because chalk sees a non-TTY stream (set `FORCE_COLOR=1` to assert styles). For app-wide context providers, wrap `render` in a small helper, and add a few PTY-level tests (**node-pty** + `strip-ansi`) that drive the built CLI for real keyboard flows. Both `ink` and `ink-testing-library` are ESM-only, so vitest is the path of least resistance over Jest.

### Debugging

- **`console.log` is not lost.** The `patchConsole` render option defaults to `true`: Ink intercepts `console.*` calls, clears the live output, renders the message above it, and repaints the UI. If console output *is* garbling the screen, something bypassed the patch — direct `process.stdout.write` calls or child-process stdio inherited straight to the terminal.
- **`render(<App />, {debug: true})`** renders every update as separate appended output instead of diffing in place — the single best tool for answering "which frame went wrong".
- **React DevTools:** install the optional `react-devtools-core` peer, run your CLI with `DEV=true`, and launch `npx react-devtools` separately to inspect the live component tree (exit the CLI manually with Ctrl+C afterwards). **This is for tree/props inspection only — don't use it to profile performance.** Ink's reconciler sets none of the flags React's Profiler needs, so treat the Profiler/flame-chart tab as unsupported.
- **High-volume tracing** goes to stderr — `useStderr().write()` preserves Ink's output — or to a file you `tail -f` in another terminal. Never stdout; Ink owns it.
- **Profiling:** `node --cpu-prof` is the real path; it writes a `.cpuprofile` on process exit, loadable in Chrome DevTools' Performance panel or `speedscope`. Common Ink-specific cost sinks: unmemoized components re-rendering on every parent update (each can trigger a fresh Yoga layout pass); `<Static>` misuse (it is for content written once and never revisited, so leaving static content out of it or putting changing content in it both hurt); and a small always-animating leaf component (such as `ink-spinner`) keeping the render cycle continuously active instead of idle between real state changes.

### Pastel — Next.js-style filesystem routing

`vadimdemedes/pastel` builds CLI command structure from filesystem layout, with Zod schemas for argument validation. Like Next.js for CLIs: each file under `commands/` is a command (`index.tsx` is `myapp`, `create.tsx` is `myapp create`, `user/add.tsx` is `myapp user add`) and exports a default React component plus optional `args`/`options` Zod schemas. Pastel 4 calls Ink's `render()` without options, so `alternateScreen`, `kittyKeyboard`, `incrementalRendering`, and `concurrent` can't be set (issue #43); full-screen apps that need them should call `render()` directly.

### Strengths and weaknesses

Ink's strengths are the declarative React model (any state library or hooks) and Yoga flexbox layout. Native alternate-screen mode since Ink 7: `render(<App />, {alternateScreen: true})` enters the alt screen and restores the terminal on exit. Inline stays the default, and the option applies only in interactive mode; it is ignored in CI or with piped stdout.

Weaknesses:
- **Heavy startup**: loading React + Yoga + the reconciler takes roughly 150–250 ms to the first frame on a modern laptop (measure yours with `hyperfine`). Bad for one-shot scripts where users expect instant response. For frequently-invoked commands (`mycli --version`, `mycli completion`), provide a fast path that bypasses Ink.
- **High-frequency re-renders used to flicker.** Ink 6.7+ ships synchronized updates (plus an opt-in Kitty keyboard protocol), which largely fixed this. When streaming LLM tokens or tailing logs, still prefer `useDeferredValue` (fully functional only with `render(<App />, {concurrent: true})`) or manual debounce; `<Static>` exists specifically to handle large append-only logs without re-rendering them. Ink 8's `incrementalRendering: true` rewrites only the changed part of each line, and a lower `maxFps` (default 30) cuts churn further.
- **Screen-reader support is opt-in and partial.** Ink 6.2 added `aria-label` and `aria-hidden` (on `<Box>` and `<Text>`), `aria-role` and `aria-state` (on `<Box>`, from fixed lists), and a screen-reader renderer that turns on only through `render(..., {isScreenReaderEnabled: true})` or `INK_SCREEN_READER=true`. Nothing detects a screen reader; `useIsScreenReaderEnabled()` only reports that flag. The renderer prints linear text without borders or color and replaces children with their `aria-label`, but it still erases and rewrites the whole live region on every change. In that mode, move finished output into `<Static>`, keep the live part small, and stop per-tick spinners and timers; Gemini CLI's `--screen-reader` mode also swaps in a separate layout and a static spinner. Design guidance: `visual-patterns.md` → *Accessibility*.

### Ink pitfalls

1. **`nodemon` breaks Inquirer/Ink arrow keys.** Use `nodemon --no-stdin` or `node --watch`.
2. **Ink 7 fixed Backspace reporting as `key.backspace`.** Old input handlers that check `key.delete` for Backspace silently break on upgrade—check `key.backspace`.
3. **Ink 8 upgrades break in three places:** percentage `minWidth`/`maxWidth` (numbers only now), `useStdout().stdout.columns` (no longer typed; use `useWindowSize()`), and `useInput` handlers that parsed mouse or focus reports (now dropped).

Raw-mode/TTY guards, CI detection, and Windows caveats apply here too — see "Cross-library pitfalls" below.

---

## Modern prompts: @clack/prompts

`@clack/prompts` has largely displaced Inquirer for new wizard-style CLIs. Stable at 1.x (bomb.sh/clack); used by **create-vite, `sv` (Svelte's CLI), and create-t3-app**. create-astro ships the same look through its own `@astrojs/cli-kit` rather than Clack.

```ts check=typescript/clack
import {intro, outro, text, confirm, select, spinner, isCancel, cancel} from '@clack/prompts';

intro('create-my-app');

const name = await text({
  message: 'Project name',
  validate: v => !v ? 'Required' : undefined,  // v is string | undefined
});
if (isCancel(name)) {
  cancel('Cancelled');
  process.exit(130);
}

const framework = await select({
  message: 'Pick a framework',
  options: [
    {value: 'react', label: 'React'},
    {value: 'vue', label: 'Vue'},
    {value: 'svelte', label: 'Svelte'},
  ],
});
if (isCancel(framework)) {
  cancel('Cancelled');
  process.exit(130);
}

const s = spinner();
s.start('Installing dependencies');
await install();
s.stop('Dependencies installed');

outro(`You're all set!`);
```

**Components:** `intro`/`outro`, `text`, `multiline`, `password`, `confirm`, `select`, `multiselect`, `groupMultiselect`, `selectKey`, `autocomplete`, `autocompleteMultiselect`, `path`, `date`, `spinner`, `progress`, `tasks`, `taskLog`, `note`, `box`, `log.info/.warn/.error/.success`, `stream`, `group`. `validate` also accepts a Standard Schema validator (Zod, Valibot, ArkType) or an async function.

**`isCancel(value)`** is critical — it detects Ctrl+C per prompt and lets you clean up gracefully. Exit 130 on cancel, not 0, so `cli && next` stops; Clack's own `cancel()` example exits 1.

Its look (connectors between prompts, single-glyph progress markers) is now a recognizable aesthetic; it is the right choice for a `create-*`-style scaffolder.

---

## @inquirer/prompts

The modern modular rewrite of Inquirer — TypeScript-first packages that replaced the legacy monolithic `inquirer`. The workhorse for prompt-heavy CLIs:

```ts check=typescript/inquirer
import {input, select, confirm, password} from '@inquirer/prompts';

try {
  const name = await input({message: 'What is your name?'});
  const role = await select({
    message: 'Choose a role',
    choices: [
      {name: 'Admin', value: 'admin'},
      {name: 'User', value: 'user'},
    ],
  });
} catch (error) {
  if (error instanceof Error && error.name === 'ExitPromptError') process.exit(130);  // Ctrl+C
  throw error;
}
```

Ctrl+C rejects the prompt with `ExitPromptError`; uncaught, it prints a stack trace in the user's terminal. Catch it as above ([recipe](https://github.com/SBoudrias/Inquirer.js/blob/ea3130ebc609a6a3910b5397244044de7eda3d05/packages/prompts/README.md#handling-ctrlc-gracefully)).

**Modular packages:** one per prompt (`@inquirer/input`, `select`, `checkbox`, `confirm`, `password`, `editor`, `search`, `number`, …); pull only what you use. i18n via `@inquirer/i18n`.

**When to choose Inquirer over Clack:** complex prompt flows with conditional questions, validation chains, custom prompt types (extensible plugin architecture), i18n requirements. **When to choose Clack over Inquirer:** modern aesthetic, minimal API, you're scaffolding (a `create-*` tool).

---

## Color libraries

| Library | Size | Speed | API | Best for |
|---|---|---|---|---|
| **picocolors** | 7 KB | Fastest single-style | Functional only: `pc.red('hi')` | Tooling internals (PostCSS, SVGO, Stylelint, Browserslist, Babel, Prettier, Vite all use it) |
| **chalk** | ~56 KB (v6) | Slower; chainable | `chalk.red.bold('hi')` | End-user CLIs with frequent chaining; truecolor; familiar |
| **kleur** | Small | Fast | Chainable | Middle ground |
| **ansis** | Small | Fastest when chaining 2+ | Chainable + truecolor | Performance-critical with chained styles |

Color-disable behavior varies by library and version. Treat `NO_COLOR`, non-TTY output, and an explicit `--color` override as an application-level output policy, then configure or bypass the styling library accordingly. chalk is ESM-only from v5 (floors and `require(esm)` in Runtime floors and ESM). For zero dependencies, `node:util` `styleText` (added in Node 20.12, stable since 22.13; honors `NO_COLOR`/TTY since 20.18/22.8; hex colors since 24.16/26.1) covers basic styling.

**picocolors for libraries / internal tools, chalk for user-facing CLIs.**

---

## Other utilities

- **ora** — single elegant spinner; 90 styles via `cli-spinners`. Use outside Ink. Inside Ink, use `<Spinner>` from `@inkjs/ui`.
- **cli-progress** — single and multi-bar progress with ETA. Use outside Ink.
- **listr2** — hierarchical animated task list with concurrency, retries, rollback. Renderers: `default` (live), `simple` (line-per-task, CI-friendly), `verbose`, `silent`, `test`. Used by Angular CLI and Electron Forge.
- **boxen** — text in boxes; used by `update-notifier` for one-time announcements ("Update available!").
- **terminal-link** — OSC 8 hyperlinks; falls back to plain URL on terminals without support.
- **string-width** — cell width for strings (handles CJK, emoji). Ink uses it internally.
- **update-notifier** — checks the npm registry for newer versions and shows a boxed notice.

---

## Argument parsers

| Parser | Adoption | Style | Best for |
|---|---|---|---|
| **commander** | The most downloaded by a wide margin | Fluent API | The default for most projects (webpack-cli, Babel CLI, Svelte's `sv`); floors in Runtime floors and ESM |
| **yargs** | Very high | Fluent + middleware | Best validation; used by Jest and nyc |
| **citty** | Growing | TS-first, declarative | UnJS ecosystem (Nuxt, Nitro, unbuild) |
| **cac** | Niche | One ~20 KB file, no deps | Vite uses it; ESM-only since v7; use ≥ 7.0.1, which fixes a prototype-pollution bug with dotted option names |
| **oclif** | Plugin marketplace | Class-per-command | Heroku, Salesforce, Shopify CLI; heaviest startup of the group |
| **node:util.parseArgs** | stdlib | Argument parsing only | Stable since Node 20; zero-dep |

**Startup overhead** grows from the stdlib parser and cac, through commander and yargs, to oclif's plugin loader. Measure your own binary with `hyperfine 'mycli --version'`.

**commander hello world:**

```ts check=typescript/commander
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

The credible new entrant, built by Anomaly: TypeScript bindings over a Zig native core via C ABI. Double-buffered rendering with alpha blending, scissor clipping, per-node hit testing for mouse. Packages: `@opentui/core` (low-level), `@opentui/react` and `@opentui/solid` (React and SolidJS renderers), and `@opentui/three` — a Three.js WebGPU renderer that rasterizes 3D scenes into terminal cells, its most differentiating capability.

Powers **opencode** (Anomaly's terminal coding agent).

**Choose if** pushing past Ink's performance ceiling — animations, real-time streaming with low latency, or complex layouts where Yoga's CPU cost matters. **Trade-off:** v0.x churn (0.6 moved layout and painting into the native core, and 0.6 and 0.7 each broke custom renderables; 0.7 also dropped the screen-sized hit grid and reads renderable hooks from the class at construction), smaller community than Ink, native binary in the install. `@opentui/core` 0.6+ declares `engines` of Bun ≥ 1.3.14 or Node ≥ 26.4. Read the [0.7.0 release notes](https://github.com/anomalyco/opentui/releases/tag/v0.7.0) before upgrading.

---

## blessed / terminal-kit

Retained-mode classics, pre-Ink era. **blessed** (ncurses in pure JS; last release 0.1.81, September 2015) is abandoned, and its fork **neo-blessed** is also unmaintained (last publish 0.2.0, June 2018). **terminal-kit** offers cursor control, screen buffers, input fields, menus, and truecolor image drawing with half-block cells (no Sixel). Choose them only for precise damage-region control or legacy code; for images prefer terminal-image (see the table at the top). **Don't choose** them for new TUI apps in 2026 — Ink is better-supported and more productive.

---

## Cross-library pitfalls

1. **ESM/CJS and Node floors.** See Runtime floors and ESM; target Node 22 or 24 and load Ink with `await import('ink')` from CommonJS.
2. **Restore terminal state on exit.** Ink: `exit()` or `unmount()`, then await `waitUntilExit()`; blessed: `screen.destroy()`. Treat OS signal listeners as an application boundary because Ink's Ctrl+C input handling does not cover SIGTERM.
3. **Detect non-TTY and CI.** `process.stdout.isTTY === false` or `process.env.CI` — degrade to plain output. Spinners and prompts must not run in CI.
4. **Raw mode requires `process.stdin.isTTY`.** Pipe input fails silently otherwise. Guard.
5. **Cell width**. Use `string-width` (Ink does); never `.length` for terminal width math.
6. **Frequently-invoked CLI startup**. Lazy-load subcommand modules. Have a fast path for `--version`/`--help`.
7. **Don't mix raw-mode libraries.** Ink + ora, Ink + blessed → broken.
8. **Windows older `cmd.exe`** doesn't support all ANSI. Target Windows Terminal.
9. **Prompts and Ink draw on stdout by default.** For a summon–choose–exit tool whose result goes to stdout, redirect the chrome: Clack takes `output: process.stderr` on each call (`intro`, `cancel` and `spinner` too), Inquirer takes `{output: process.stderr}` as its second argument, and Ink takes `render(<App />, {stdout: process.stderr})`.

---

## Stack recommendations by project shape

| Project shape | Stack |
|---|---|
| Simple non-interactive CLI (~50 ms cold start, 19 packages, under 1 MB installed) | `commander + picocolors + ora` |
| Interactive setup wizard (`create-*` tool) | `@clack/prompts + picocolors + commander` |
| Complex CLI with tasks | `commander + @inquirer/prompts + listr2 + chalk + boxen + update-notifier` |
| Full TUI app | `ink + @inkjs/ui + zustand + commander + ink-testing-library` |
| Heroku-class plugin CLI | `oclif + ink + chalk + listr2` |
| Performance-critical / animated TUI | `@opentui/core` or `@opentui/react` |

---
