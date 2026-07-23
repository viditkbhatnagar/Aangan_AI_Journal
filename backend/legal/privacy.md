# Aangan Privacy Policy

**Version 2026-07-23 · Draft for pilot use — review by counsel before public launch.**

Aangan is a private family voice journal. Privacy is the product: everything
you record is private to you by default, and only you can share it.

## 1. What we collect, and why

| Data | Purpose |
|---|---|
| Account details (name, email, hashed password, language) | Sign-in and personalisation |
| Voice recordings you make | Transcription so your entry can be saved as text |
| Journal transcripts, summaries, and extracted notes ("facts") | The core journal; answering your family's questions from what you chose to share |
| Sharing rules, alert triggers, and share choices | Carrying out exactly the sharing you asked for |
| Actions you ask us to prepare | Preparing them for your approval |
| Basic product events (sign-in time, feature used) | Keeping the service working and improving it — first-party only, no ad trackers |

We do not collect data we don't need, and we never sell personal data.

## 2. Who processes your data

Your journal is stored on the Aangan server (database, vector index, and audio
files). Two kinds of processing leave that server, **only when the relevant
feature is configured**:

- **Voice transcription:** your audio recording is sent to **Deepgram** to be
  converted to text.
- **AI summaries and answers:** your entry text (or a question plus the shared
  snippets you are allowed to see) is sent to our language-model provider —
  **OpenAI or OpenRouter**, or **Anthropic** — to produce the summary or reply.

Another family member's **private** content is never included in any AI request
made on your behalf — this is enforced in code, not by policy alone.

## 3. Sharing inside your family

Everything starts private. Content becomes visible to others only when you
explicitly share it, or when a standing rule **you yourself created** applies.
You can un-share at any time, and un-sharing takes effect immediately.

## 4. Retention and deletion

- You can delete any journal entry at any time; deletion removes the entry, its
  extracted notes, its share grants, alerts it caused, its search vectors, and
  the audio file.
- You can delete your entire account and all your content.
- Backups are rotated; deleted content leaves backups on the backup schedule
  described in our operations documentation.

## 5. Your rights

Access, correction, export, and deletion of your own data — available in-app
(Me → export / delete) or by contacting us. We aim to answer within 7 days.

## 6. Age

Aangan is for adults (18+) during the pilot. Do not create accounts for minors.

## 7. Security

Passwords are stored hashed (bcrypt); sessions use signed tokens kept only in
memory in your browser; access to another member's private content is blocked
at the retrieval layer and covered by automated tests. No system is perfectly
secure; we will notify affected users of any breach without undue delay.

## 8. Contact

Questions or requests: use Me → Help & feedback in the app.
