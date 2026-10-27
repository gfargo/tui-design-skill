# TypeScript / JavaScript ecosystem — Ink, Clack, Inquirer

Node splits into pretty CLIs (argument parsing, color, prompts, spinners) and full TUIs, and into imperative versus declarative (React-style) APIs. **Ink has effectively won the high-end TUI space.** It powers Claude Code (publicly TypeScript + React + Ink + Yoga + Bun), GitHub Copilot CLI, Gemini CLI, and Cloudflare Wrangler.

**Contents:**
- [Quick recommendation](#quick-recommendation) · [Runtime floors and ESM](#runtime-floors-and-esm)
- [Ink](#ink-vadimdemedesink) — [Lifecycle and terminal handoff](#lifecycle-and-terminal-handoff) · [Primitives](#primitives) · [Layout](#layout) · [Hooks](#hooks) · [Lists, focus, and tables](#lists-focus-and-tables) · [Long-running work and Ctrl+C](#long-running-work-and-ctrlc) · [ink-ui](#ink-ui-vadimdemedesink-ui) · [Testing](#testing--ink-testing-library) · [Debugging](#debugging) · [Pastel](#pastel--nextjs-style-filesystem-routing) · [Strengths and weaknesses](#strengths-and-weaknesses) · [Ink pitfalls](#ink-pitfalls)
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
| Argument parsing | **commander** (de facto default); yargs, oclif, citty, cac: see Argument parsers |
| Terminal colors | **picocolors** (fast, functional) or **chalk** (classic chainable API) |
| Beyond Ink's perf ceiling | **OpenTUI** (Zig-backed, v0.x) |
| Image rendering in terminal | **terminal-image** 5 (Kitty/iTerm2 protocols, half-block fallback) |

**Default full-TUI stack: Ink + @inkjs/ui + zustand + commander + ink-testing-library** (the last two UI/test packages are unmaintained but work with Ink 8; see ink-ui and Testing).

## Runtime floors and ESM

Node 20 is end-of-life; target Node 22 or 24 (check the Node release schedule). The current majors below need Node 22; use the last Node 20 line only as a bridge for a deployment that can't move yet.

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

Ink 7.1+ (unchanged in 8.0) distinguishes permanent unmounting from a resumable terminal suspension (`suspendTerminal` is not in 7.0 or Ink 6). Keep signal policy at the render boundary and temporary ownership changes inside `useApp()`.

| Boundary | Ink 7.1+ contract |
|---|---|
| Normal exit | Use `useApp().exit(...)` inside the tree or the render handle's `unmount()` outside it. At the top level, await `waitUntilExit()` before post-run output or process termination so pending terminal writes finish. |
| SIGINT / SIGTERM | `exitOnCtrlC` handles Ctrl+C bytes while stdin is raw; it is not a SIGTERM handler. If the host requires graceful signals, register them once at the process boundary, unmount, await `waitUntilExit()`, set the exit status, and remove listeners. Do not call `process.exit()` before cleanup flushes. To cancel work on the first Ctrl+C, see *Long-running work and Ctrl+C*. |
| Interactive child | Use `await suspendTerminal(async () => runChild())`. Ink pauses input and rendering, restores terminal modes, runs the callback even without an interactive TTY, and re-enters with a full redraw in `finally`. Reload child-mutated data afterward because redraw preserves the existing React state. For the manual form, always `await suspension.resume()` in `finally` or use `await using`. Do not unmount. |
| Foreground suspend | Ink has no separate high-level job-control action. If a Unix-only Ctrl+Z feature is necessary, perform SIGTSTP inside `suspendTerminal` and let its resume path re-enter and redraw; expose a different action on Windows. |

The tagged [`suspendTerminal` documentation](https://github.com/vadimdemedes/ink/blob/v8.0.0/readme.md#suspendterminalcallback) covers callback, manual, non-interactive, and nesting behavior. A second overlapping suspension is an error, so centralize ownership.

**Inline or alternate screen.** Inline is the default: the live region sits in the scrollback, and permanent lines go above it through `<Static>`, `useStdout().write()`, or the patched `console.*`. `render(<App />, {alternateScreen: true})` (Ink 7+) enters the alternate screen and restores the terminal on exit. It applies only in interactive mode (ignored in CI or with piped stdout), and teardown-time output is discarded, so print the final summary after `await waitUntilExit()`.

### Primitives

Ink ships only a handful of components — everything else composes from these:

- **`<Text>`** — only place strings can live. Props: `color`, `backgroundColor`, `bold`, `italic`, `underline`, `inverse`, `dimColor`, `wrap`, `strikethrough`. Strings as direct children of `<Box>` will throw — they must be wrapped.
- **`<Box>`** — flexbox container. Props: `padding`, `paddingX/Y/Top/Right/Bottom/Left`, `margin*`, `borderStyle`, `borderColor`, `borderTop`/`Bottom`/`Left`/`Right` (selective borders), `width`, `height`, `minWidth`/`maxWidth` (numbers only in Ink 8), `flexDirection`, `flexGrow`, `flexShrink`, `flexBasis`, `justifyContent`, `alignItems`, `gap`, `display: 'flex' | 'none'`, `overflow`/`overflowX`/`overflowY`. Ink 8 adds `contentOffsetX`/`contentOffsetY` for scrolling: give a fixed-height viewport `overflow="hidden"`, wrap the content in a `flexShrink={0}` box that carries any padding, and clamp the offset to `content.height - clientHeight` from `useBoxMetrics()`. That suits modest content; for long lists see *Lists, focus, and tables*.
- **`<Newline>`** — newline characters; only valid inside `<Text>` (use `gap` or margin between boxes). **`<Spacer>`** — flex-grow filler.
- **`<Static>`** — renders items permanently above the live UI; once rendered, never re-renders. Suited to log streaming.
- **`<Transform>`** — wraps children and transforms their rendered string. Used for gradients and OSC 8 hyperlinks.

### Layout

Yoga (Meta's open-source flexbox engine, same as React Native). No CSS, no className — props on `<Text>` and `<Box>`. Border styles come from `cli-boxes`: `single`, `double`, `round`, `bold`, `singleDouble`, `doubleSingle`, `classic`, or a custom `BoxStyle` object.

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
- **`useInput((input, key) => ...)`** — keyboard events. `key` is `{upArrow, downArrow, leftArrow, rightArrow, return, escape, tab, backspace, delete, ctrl, shift, meta, pageUp, pageDown, home, end}` (plus Kitty-protocol extras). Ink 8 drops mouse, focus, and cursor-position reports rather than passing them as typed text, so mouse support must parse raw stdin.
- **`useApp()`** — `{exit(errorOrResult?), waitUntilRenderFlush (7+), suspendTerminal (7.1+)}`. Pass an `Error` to `exit` to reject the render handle's `waitUntilExit()`; there is no separate error variant. Use `suspendTerminal` for a resumable interactive child, not final shutdown.
- **`useStdin()`** — `{stdin, setRawMode, isRawModeSupported}`. **`useStdout()`** / **`useStderr()`** — write outside the live UI; Ink 8 types the streams generically, so read the size from `useWindowSize()`, not `stdout.columns`.
- **`useFocus({autoFocus, isActive, id})`** — Tab-focusable component. **`useFocusManager()`** — `{focus(id), focusNext, focusPrevious, enableFocus, disableFocus, activeId (7+)}`.
- **`useWindowSize()`** (7+) — `{columns, rows}`, updates on resize. **`useCursor()`** — position the real terminal cursor (IME-friendly input).
- **`usePaste(callback)`** (7+) — bracketed-paste events, so pasted text arrives as one chunk instead of spraying through `useInput` character by character.
- **`useAnimation()`** (7+) — frame ticker; `isActive: false` stops it, and turning it back on resets the counters to 0 (it does not resume). **`useBoxMetrics()`** (7+) — measured box size; Ink 8 adds `clientWidth`/`clientHeight`, the size inside its borders.

Standard React hooks all work. For larger apps use **Zustand** (recommended), **Jotai**, or `useReducer` + Context.

### Lists, focus, and tables

- **Virtualize by slicing.** `contentOffsetY` only shifts and clips: Yoga still lays out and Ink still paints every child, so 20,000 rows cost 20,000 rows per frame. Mount only `items.slice(top, top + height)` in a fixed-height box.
- **Every mounted `useInput` fires on every key** unless its `isActive` is false. `useFocus` only tracks which component Tab selected; it mutes nothing. Gate each handler with `{isActive: isFocused}` (or a mode flag, so the list behind a dialog stops moving).
- **Tables keep one row to one line**, which the slice math assumes: give each cell a fixed-`width` `<Box>` and `<Text wrap="truncate-end">`. The default `wrap` grows the row.

```tsx check=typescript/ink-virtual-list
import React, {useState} from 'react';
import {Box, Text, useFocus, useInput} from 'ink';

const VirtualList = ({items, height, width}: {items: string[]; height: number; width: number}) => {
  const {isFocused} = useFocus();
  const [selected, setSelected] = useState(0);
  useInput((_input, key) => {
    if (key.downArrow) setSelected(i => Math.min(items.length - 1, i + 1));
    if (key.upArrow) setSelected(i => Math.max(0, i - 1));
  }, {isActive: isFocused});

  const top = Math.max(0, Math.min(selected - Math.floor(height / 2), items.length - height));
  return (
    <Box flexDirection="column" width={width} height={height}>
      {items.slice(top, top + height).map((item, i) => (
        <Text key={top + i} wrap="truncate-end" inverse={isFocused && top + i === selected}>{item}</Text>
      ))}
    </Box>
  );
};
```

### Long-running work and Ctrl+C

Ink renders, reads keys, and runs timers on one event loop. `execSync`, `spawnSync`, `readFileSync` on a big file, or a long CPU loop freezes the spinner and queues keystrokes until it returns. Use `execFile`/`spawn`, `fs/promises`, or a worker thread, plus an `AbortSignal`.

By default Ink quits on Ctrl+C before `useInput` sees it. For "first cancels, second quits", pass `exitOnCtrlC: false` and handle `key.ctrl && input === 'c'` in an always-active `useInput`: with no active input hook raw mode is off and Ctrl+C is SIGINT again.

```tsx check=typescript/ink-cancel
import React, {useEffect, useRef, useState} from 'react';
import {render, Text, useAnimation, useApp, useInput} from 'ink';
import {execFile} from 'node:child_process';

const Build = ({cmd, args}: {cmd: string; args: string[]}) => {
  const {exit} = useApp();
  const [status, setStatus] = useState('running');
  const abort = useRef(new AbortController());
  const {frame} = useAnimation({interval: 80, isActive: status === 'running'});
  useEffect(() => {
    execFile(cmd, args, {signal: abort.current.signal}, error => setStatus(error ? 'stopped' : 'done'));
  }, []);
  useInput((input, key) => {
    if (!key.ctrl || input !== 'c') return;
    if (status === 'running') abort.current.abort();  // first Ctrl+C cancels
    else {
      process.exitCode = 130;                         // second quits
      exit();
    }
  });

  return <Text>{status === 'running' ? `${'|/-\\'[frame % 4]} ${cmd}` : status}</Text>;
};

render(<Build cmd="npm" args={['run', 'build']} />, {exitOnCtrlC: false});
```

### ink-ui (vadimdemedes/ink-ui)

The companion library of themeable widgets:

- `<TextInput>`, `<EmailInput>`, `<PasswordInput>` — uncontrolled inputs: `defaultValue`, `onChange`, `onSubmit`, and no `value` prop (issue #20), so remount with a new `key` to clear one. Every input listens to every key unless `isDisabled`, and none integrates with `useFocus`: pass `isDisabled={!isFocused}`.
- `<Select>`, `<MultiSelect>`, `<ConfirmInput>` (y/n), `<ProgressBar>`, `<Badge>`, `<StatusMessage>`, `<Alert>`, and `<Spinner>` (use it inside Ink, not `ora`).

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

`renderToString()` (Ink 6.8+) renders synchronously for tests. **Staleness caveat.** ink-testing-library 4.0.0 was built against Ink 5 / React 18 (May 2024; unmaintained and still the latest release) but installs and works with Ink 6.8, 7.1, and 8. `stdin.write` drives `useInput` and `usePaste` as long as the test awaits after each write, because frames update asynchronously (the "stdin.write() does not trigger useInput" report reproduces only on Ink 5.0.1). Frames are text only because chalk sees a non-TTY stream (set `FORCE_COLOR=1` to assert styles). Add a few PTY-level tests (**node-pty** + `strip-ansi`) for real keyboard flows. Both packages are ESM-only; prefer vitest over Jest.

### Debugging

- **`console.log` is not lost.** The `patchConsole` render option defaults to `true`: Ink intercepts `console.*`, renders the message above the live output, and repaints. If console output *is* garbling the screen, something bypassed the patch: direct `process.stdout.write` or child-process stdio inherited straight to the terminal.
- **`render(<App />, {debug: true})`** renders every update as separate appended output instead of diffing in place, the best tool for "which frame went wrong".
- **React DevTools:** install the optional `react-devtools-core` peer, run your CLI with `DEV=true`, and launch `npx react-devtools` separately to inspect the live component tree. **Tree/props inspection only, not profiling:** Ink's reconciler sets none of the flags React's Profiler needs.
- **High-volume tracing** goes to stderr (`useStderr().write()`) or a file you `tail -f`, never stdout; Ink owns it.
- **Profiling:** `node --cpu-prof` is the real path; it writes a `.cpuprofile` on exit, loadable in Chrome DevTools' Performance panel or `speedscope`. Common Ink cost sinks: unmemoized components re-rendering on every parent update; `<Static>` misuse (static content left out of it, or changing content put in it); a mounted-but-hidden long list (see *Lists, focus, and tables*); and an always-animating leaf such as `ink-spinner` keeping the render cycle busy.

### Pastel — Next.js-style filesystem routing

`vadimdemedes/pastel` builds the command tree from the filesystem: each file under `commands/` is a command (`index.tsx` is `myapp`, `user/add.tsx` is `myapp user add`) exporting a default React component plus optional `args`/`options` Zod schemas. Pastel 4 calls Ink's `render()` without options, so `alternateScreen`, `kittyKeyboard`, `incrementalRendering`, and `concurrent` can't be set (issue #43); call `render()` directly when you need them.

### Strengths and weaknesses

Ink's strengths are the declarative React model and Yoga flexbox layout. Weaknesses:
- **Heavy startup**: roughly 150–250 ms to the first frame (measure with `hyperfine`); give `--version` and completion commands a fast path that bypasses Ink.
- **High-frequency re-renders used to flicker.** Ink 6.7+ ships synchronized updates, which largely fixed this. When streaming LLM tokens or tailing logs, still prefer `useDeferredValue` (fully functional only with `render(<App />, {concurrent: true})`) or manual debounce, and `<Static>` for append-only logs. Ink 8's `incrementalRendering: true` rewrites only the changed part of each line, and a lower `maxFps` (default 30) cuts churn further.
- **Screen-reader support is opt-in and partial.** Ink 6.2 added `aria-label` and `aria-hidden` (on `<Box>` and `<Text>`), `aria-role` and `aria-state` (on `<Box>`, from fixed lists), and a screen-reader renderer that turns on only through `render(..., {isScreenReaderEnabled: true})` or `INK_SCREEN_READER=true`. Nothing detects a screen reader; `useIsScreenReaderEnabled()` only reports that flag. The renderer prints linear text without borders or color and replaces children with their `aria-label`, but it still erases and rewrites the whole live region on every change. In that mode, move finished output into `<Static>`, keep the live part small, and stop per-tick spinners and timers. Design guidance: `visual-patterns.md` → *Accessibility*.

### Ink pitfalls

1. **`nodemon` breaks Inquirer/Ink arrow keys.** Use `nodemon --no-stdin` or `node --watch`.
2. **Ink 7 fixed Backspace reporting as `key.backspace`.** Old input handlers that check `key.delete` for Backspace silently break on upgrade—check `key.backspace`.
3. **Ink 8 upgrades break in three places:** percentage `minWidth`/`maxWidth` (numbers only now), `useStdout().stdout.columns` (no longer typed; use `useWindowSize()`), and `useInput` handlers that parsed mouse or focus reports (now dropped).

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

**Components:** `intro`/`outro`, `text`, `password`, `confirm`, `select`, `multiselect`, `autocomplete`, `path`, `date`, `spinner`, `progress`, `tasks`, `note`, `log.*`, `group`, and more. `validate` also accepts a Standard Schema validator (Zod, Valibot, ArkType) or an async function.

**`isCancel(value)`** is critical — it detects Ctrl+C per prompt and lets you clean up gracefully. Exit 130 on cancel, not 0, so `cli && next` stops; Clack's own `cancel()` example exits 1. Its look suits a `create-*` scaffolder.

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

It ships one package per prompt (`@inquirer/input`, `select`, `checkbox`, …). **Inquirer over Clack:** complex flows with conditional questions, validation chains, custom prompt types, i18n. **Clack over Inquirer:** minimal API and look, scaffolding a `create-*` tool.

## Color libraries

| Library | Size | Speed | API | Best for |
|---|---|---|---|---|
| **picocolors** | 7 KB | Fastest single-style | Functional only: `pc.red('hi')` | Tooling internals (PostCSS, SVGO, Stylelint, Browserslist, Babel, Prettier, Vite all use it) |
| **chalk** | ~56 KB (v6) | Slower; chainable | `chalk.red.bold('hi')` | End-user CLIs with frequent chaining; truecolor; familiar |

Color-disable behavior varies by library and version, so treat `NO_COLOR`, non-TTY output, and an explicit `--color` override as an application-level output policy and configure or bypass the library accordingly. chalk is ESM-only from v5 (see Runtime floors and ESM). For zero dependencies, `node:util` `styleText` (added in Node 20.12, stable since 22.13; honors `NO_COLOR`/TTY since 20.18/22.8; hex colors since 24.16/26.1) covers basic styling.

## Other utilities

- **ora** — single spinner (outside Ink; inside it use `<Spinner>` from `@inkjs/ui`). **cli-progress** — single and multi-bar progress with ETA (outside Ink).
- **listr2** — hierarchical animated task list with concurrency, retries, rollback. Renderers: `default` (live), `simple` (line-per-task, CI-friendly), `verbose`, `silent`, `test`. Used by Angular CLI and Electron Forge.
- **boxen** — text in boxes. **update-notifier** — checks the npm registry for newer versions and shows a boxed notice. **terminal-link** — OSC 8 hyperlinks with a plain-URL fallback. **string-width** — cell width for strings (CJK, emoji).

## Argument parsers

| Parser | Adoption | Style | Best for |
|---|---|---|---|
| **commander** | The most downloaded by a wide margin | Fluent API | The default (webpack-cli, Babel CLI, Svelte's `sv`); floors in Runtime floors and ESM |
| **yargs** | Very high | Fluent + middleware | Best validation; used by Jest and nyc |
| **citty** | Growing | TS-first, declarative | UnJS ecosystem (Nuxt, Nitro, unbuild) |
| **cac** | Niche | One ~20 KB file, no deps | Vite uses it; ESM-only since v7; use ≥ 7.0.1, which fixes a prototype-pollution bug with dotted option names |
| **oclif** | Plugin marketplace | Class-per-command | Heroku, Salesforce, Shopify CLI; heaviest startup of the group |
| **node:util.parseArgs** | stdlib | Argument parsing only | Stable since Node 20; zero-dep |

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

With any `async` action, call `await program.parseAsync()`: `parse()` returns before the action settles, so a rejection escapes as an unhandled rejection. For an Ink action, `await` the render handle's `waitUntilExit()` inside it.

## OpenTUI (anomalyco/opentui)

The credible new entrant, built by Anomaly: TypeScript bindings over a Zig native core. Double-buffered rendering with alpha blending, scissor clipping, per-node mouse hit testing. Packages: `@opentui/core` (low-level), `@opentui/react` and `@opentui/solid` (React and SolidJS renderers), and `@opentui/three` (a Three.js WebGPU renderer that rasterizes 3D scenes into terminal cells).

Powers **opencode** (Anomaly's terminal coding agent). **Choose if** pushing past Ink's performance ceiling — animations, real-time streaming with low latency, or complex layouts where Yoga's CPU cost matters. **Trade-off:** v0.x churn (0.6 moved layout and painting into the native core, and 0.6 and 0.7 each broke custom renderables; 0.7 also dropped the screen-sized hit grid and reads renderable hooks from the class at construction), a smaller community, and a native binary in the install. `@opentui/core` 0.6+ declares `engines` of Bun ≥ 1.3.14 or Node ≥ 26.4. Read the [0.7.0 release notes](https://github.com/anomalyco/opentui/releases/tag/v0.7.0) before upgrading.

## blessed / terminal-kit

Retained-mode classics, pre-Ink era. **blessed** (ncurses in pure JS; last release 0.1.81, September 2015) is abandoned, and its fork **neo-blessed** is also unmaintained (last publish 0.2.0, June 2018). **terminal-kit** offers cursor control, screen buffers, input fields, menus, and half-block truecolor images (no Sixel). Choose them only for precise damage-region control or legacy code; prefer Ink for new TUI apps.

## Cross-library pitfalls

1. **Restore terminal state on exit.** Ink: `exit()` or `unmount()`, then await `waitUntilExit()`; blessed: `screen.destroy()`. Ink's Ctrl+C handling does not cover SIGTERM (see Lifecycle). ESM/CJS and Node floors: see Runtime floors and ESM.
2. **Detect non-TTY and CI** (`process.stdout.isTTY === false`, `process.env.CI`) and degrade to plain output; spinners and prompts must not run there. Raw mode needs `process.stdin.isTTY`; guard it.
3. **Cell width**: use `string-width` (Ink does), never `.length`.
4. **Frequently-invoked CLI startup**: lazy-load subcommand modules and give `--version`/`--help` a fast path.
5. **Don't mix raw-mode libraries** (Ink + ora, Ink + blessed → broken). Older `cmd.exe` lacks some ANSI; target Windows Terminal.
6. **Prompts and Ink draw on stdout by default.** For a summon–choose–exit tool whose result goes to stdout, redirect the chrome: Clack takes `output: process.stderr` on each call (`intro`, `cancel` and `spinner` too), Inquirer takes `{output: process.stderr}` as its second argument, and Ink takes `render(<App />, {stdout: process.stderr})`.

## Stack recommendations by project shape

| Project shape | Stack |
|---|---|
| Simple non-interactive CLI (~50 ms cold start, 19 packages, under 1 MB installed) | `commander + picocolors + ora` |
| Interactive setup wizard (`create-*` tool) | `@clack/prompts + picocolors + commander` |
| Complex CLI with tasks | `commander + @inquirer/prompts + listr2 + chalk + boxen + update-notifier` |
| Full TUI app | `ink + @inkjs/ui + zustand + commander + ink-testing-library` |
| Heroku-class plugin CLI | `oclif + ink + chalk + listr2` |
| Performance-critical / animated TUI | `@opentui/core` or `@opentui/react` |
