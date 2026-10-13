`INK_SCREEN_READER=true` enables Ink’s screen reader rendering mode; it doesn’t turn your chat into an incremental announcement feed.

The likely problem is **what remains in the live render tree and how often it changes**. A transcript rendered as ordinary `<Text>` stays part of subsequent renders. Streaming tokens, spinner frames, and status changes repeatedly update that tree, so NVDA can encounter the conversation again. A spinner adds frequent updates even when there’s no useful new information to announce.

Change the rendering strategy:

- **Put completed messages in `<Static>`.** Append each message once, with a stable ID. Keep finalized content immutable. Don’t put the entire transcript in the live panel.
- **Stop spinner animation in screen reader mode.** Replace it with a plain status such as “Generating response.” Disable its timer or unmount the animated component; merely hiding its text can leave updates running.
- **Buffer streaming output for accessible mode.** Emit the completed response once, or append deliberate sentence-sized chunks. Don’t repeatedly rewrite the growing response.
- **Keep the live panel small.** Limit it to the current input and essential status. Avoid repeatedly changing decorative counters, elapsed time, or progress text.
- **Use Ink’s accessibility labels and hiding features for meaning and decoration**, but don’t expect them to deduplicate transcript updates. Terminal output is not a browser ARIA live region.

Conceptually:

```jsx
<>
  <Static items={completedMessages}>
    {message => (
      <Text key={message.id}>
        {message.role}: {message.text}
      </Text>
    )}
  </Static>

  {generating && (
    screenReaderEnabled
      ? <Text>Generating response.</Text>
      : <AnimatedSpinner />
  )}

  {!screenReaderEnabled && <StreamingPreview />}
  <ChatInput />
</>
```

Use the same screen reader setting that Ink uses to select this behavior, including any explicit render-option override.

**Verify with NVDA in the actual Windows terminal your users run:** leave generation active for several seconds, complete a response, then type another prompt. The status should not chatter, the response should be announced once, and old messages should remain available for review without being re-emitted.

There are no app files in this workspace, so this is a diagnosis of the reported pattern rather than a confirmed code-level finding.