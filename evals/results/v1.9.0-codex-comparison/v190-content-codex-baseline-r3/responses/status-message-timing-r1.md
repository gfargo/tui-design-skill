A good default is **4 seconds for routine messages; errors stay until acknowledged or resolved**.

| Message | Duration | Behavior |
|---|---|---|
| Routine success (“Saved”) | 3–5 seconds | Return to the normal status line |
| Progress (“Uploading…”) | Until complete | Replace with success or failure |
| Warning requiring action | Until addressed or dismissed | Show the next action |
| Error | Until acknowledged or resolved | Keep accessible details and a retry path |

Errors shouldn’t disappear on a timer or be overwritten by routine updates. Show a concise explanation and recovery action, such as **“Save failed: disk full. [r] Retry · [Esc] Dismiss.”**

Dismissing an error should clear the banner, not erase the record. Keep it in a message history or log. Reserve modal dialogs for errors that block further interaction.