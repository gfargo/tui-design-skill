No—`bubbletea.MakeRenderer(sess)` belongs to the **Wish v1 / Lip Gloss v1** approach. Lip Gloss v2 no longer uses per-session renderers.

With **Wish v2’s Bubble Tea middleware**, create a separate Tea program for each SSH session and let the middleware configure its terminal environment and color profile. Use ordinary Lip Gloss v2 styles; Bubble Tea v2 converts their colors to the client’s supported profile when rendering.

A few practical points:

- Use the v2 packages consistently: `charm.land/wish/v2/bubbletea`, `charm.land/bubbletea/v2`, and `charm.land/lipgloss/v2`.
- Avoid detecting a profile from the server’s stdout or setting a process-wide profile.
- If your model needs to choose different palettes by capability, handle `tea.ColorProfileMsg` and keep that information in the session’s model.
- Light/dark background detection is separate from color capability; handle `tea.BackgroundColorMsg` if you need adaptive palettes.

I couldn’t retrieve the current upstream source from this environment, so I can’t verify the exact APIs in your installed releases.