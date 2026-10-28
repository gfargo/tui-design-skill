For a new CLI, I’d target **Ink 6.x, React 19.x, and Node 24 LTS**. Ink 6’s compatibility floor is Node 20 and React 19; Node 20 is already end-of-life, so avoid it for a new project. Use ESM (`"type": "module"`).

Yes, you can still read:

```tsx
const {stdout} = useStdout();
const columns = stdout.columns ?? 80;
```

But reading that property **doesn’t subscribe your component to terminal resizes**. For responsive layouts, use Ink’s dedicated hook in versions that provide it:

```tsx
import {useWindowSize} from 'ink';

const {columns, rows} = useWindowSize();
```

I couldn’t reach the live registry or docs here, so treat those as recommended major versions, not a verified claim about today’s latest releases.