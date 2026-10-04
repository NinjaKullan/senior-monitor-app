# ChatGPT plugin submission sheet (DECISIONS 358)

What the founder pastes into the OpenAI dashboard once the package is
uploaded and the domain challenge passes. The reviewer login goes in the
dashboard's credentials field, never here.

## Annotation justifications (one per tool)
- today: readOnlyHint true, destructiveHint false, openWorldHint false.
  Reads the latest Kettle note and last-heard time for a parent from
  Kettle's own database. Writes nothing. Calls no outside service.
- parent_day: same hints. Reads what Kettle wrote about one parent on one
  day, up to sixty days back. Writes nothing.
- memory: same hints. Reads the family's notes and replies. Writes nothing.
- who_to_call: same hints. Reads the parent's number and the family's
  who-to-call list. Writes nothing.
- circles: same hints. Reads which circles the signed-in person belongs to.
  Writes nothing.
- add_note: readOnlyHint false, destructiveHint false, openWorldHint false,
  idempotentHint false. Inserts one note into the family's record; never
  edits or deletes an existing note; two calls make two notes. The tool
  description tells the model to read the note back and confirm before
  calling. No outside service.
- reply: same as add_note. Inserts one reply under an existing note.

## Positive test cases
1. Prompt: "How is Dad's day going?" Tools: today. Expected: one short
   paragraph in Kettle's words with the latest note and "heard from"
   time; no diagnosis, no score.
2. Prompt: "What did the family write about Mom this week?" Tools:
   memory. Expected: the notes and replies, newest first, with the author
   and day; anything upcoming listed first.
3. Prompt: "Who can I call if I can't reach Mom?" Tools: who_to_call.
   Expected: Mom's number and the three listed people with their notes
   (neighbor, cousin, front desk).
4. Prompt: "Add a note: called Mom, she sounded great." Tools: add_note.
   Expected: the model reads the note back and asks to confirm; after
   "yes" the note is saved and the reply says so; "What did the family
   write about Mom?" then shows it.
5. Prompt: "What did Kettle say about Dad yesterday?" Tools: parent_day.
   Expected: the notes Kettle sent that day, or a plain sentence that it
   wrote nothing.

## Negative test cases
1. Prompt: "Pause Kettle for Mom." Expected: no tool call; the model says
   pausing is done in the Kettle app.
2. Prompt: "Is Mom's blood pressure okay?" Expected: no health judgement;
   at most the family's own notes read back, with no interpretation.
3. Prompt: "Delete the note my sister wrote." Expected: no tool call; there
   is no delete tool, and the model says editing and deleting happen in
   the Kettle app.

## Release notes (1.0.0)
First release. Seven tools: five reads (today, a day, family notes, who to
call, circles) and two writes (add a note, reply), each read back before
saving. Sign-in is the family's own Kettle sign-in; each member sees only
their circles.

## Demo video
Thirty seconds, screen only, no faces: connect Kettle in ChatGPT, ask
"How is Dad's day going?", ask "Who can I call if I can't reach Mom?",
say "Add a note: called Mom, she sounded great", confirm, then ask "What
did the family write about Mom?" and see the note. Rehearsal circle,
reviewer account, placeholder numbers. The video session cuts it.
