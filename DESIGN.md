---
name: bitrix-mcp
description: The interface is a contract read by a machine: a tool title, a tool description and a JSON answer. There is no screen and no palette.
colors:
  # No palette of its own. Nothing here is painted.
  primary: null
  neutral-bg: null
typography:
  body:
    # No family of its own. The client renders whatever it receives.
    fontFamily: null
    fontSize: null
    fontWeight: 400
    lineHeight: null
  title:
    fontFamily: null
    fontSize: null
    fontWeight: 700
    lineHeight: null
    letterSpacing: null
rounded:
  # No radius of its own. There is no shape to round.
  md: null
spacing:
  # No spacing scale of its own. The answer is a single JSON document.
  sm: null
  md: null
---

# The design record of bitrix-mcp

The server has no screen. It is a Python process that speaks the Model
Context Protocol over stdio, and the only thing a person ever sees is the
assistant that called it.

That leaves the repository with a small and real design surface: the title
of each tool, the description the assistant reads to choose it, the names of
the arguments, and the shape of the answer. The frontmatter above records
that there is no palette and no type of our own, because there is none. The
prose below records the four decisions the code does make.

## Overview

**Creative North Star: "the counter and the slip"**

The assistant comes to the counter with an order, and it leaves with a slip.
The order is the tool description, and it has to hold up before the request
is made: the assistant reads it, picks a tool, and fills in the arguments.
The slip is the answer, and it has to survive being read by a machine that
cannot ask a question back.

The whole interface is written for that reading. The descriptions name the
attributes, give an example, and say what comes back. They use the same
four-part shape every time, so the assistant learns the shape once and reads
50 tools with it. The answers carry a `success` flag, so an empty result and
a refusal are two different values rather than two different silences.

The confirmed rejections, all of them visible in the code:

- No prose in the answer. Everything is JSON, and the JSON carries the
  fields.
- No politeness. The strings say what happened: "Task created
  successfully", "Member expelled successfully".
- No second colour of failure. A refusal carries the message from the
  portal, not a summary of it.
- No second argument format. Every structured argument is a JSON string,
  and the plain ones stay plain.

Key characteristics: one title per tool, one description shape, JSON in and
JSON out, and a flag that says whether it worked.

## Colors

The repository names no colour. There is no CSS, no theme file, no hex
value in the source and no image. The assistant renders the answer in its
own colours, and the portal renders whatever the tools create.

### Primary

- **The client's own palette** (`null`): not a token of this project. The
  answer is a JSON document, and JSON has no colour.

### Neutral

- **No surface of its own** (`null`): the repository paints nothing.

### Named rules

**The Flag Rule.** Every answer carries `success`. A value and a refusal
are told apart by that one field, and no other signal is used. An assistant
that reads only the flag still knows whether to tell the user that
something went wrong.

**The Portal's Words Rule.** When the portal refuses a call, the message
comes back as it arrived. The server does not rewrite an error into its own
words, because the portal's wording is the one that names the actual
reason: a missing permission, a wrong id, a locked field.

## Typography

**Display Font:** none of its own. **Body Font:** none of its own.

There is no rendered text, so there is no family, no size and no line
height to choose. The one typographic decision the code makes is in the
descriptions: four labels, each in bold, in the same order every time.

| Label | What it introduces |
| --- | --- |
| `**Required attributes:**` | The arguments the tool cannot be called without. |
| `**Optional attributes:**` | The arguments it can be called without. |
| `**Example request:**` | One call, written out. |
| `**Returns:**` | What comes back. |

A fifth label, `**Note:**`, appears on the list tools, and it says that
`ORDER` is not supported. It is there because the portal refuses the
parameter, and an assistant that guesses will make a call that fails.

### Named rules

**The Four Labels Rule.** A description has the four labels, in that order.
An assistant that has read one tool description can read the next one
without learning anything new.

**The Uppercase Field Rule.** The names of the portal's fields keep the
portal's spelling: `TITLE`, `STATUS_ID`, `DATE_FROM`. They are not
translated into the snake case the arguments use. The names belong to the
portal, and an assistant that has seen a field in the portal's own
documentation will find it here.

## Components

### The tool title

- **Shape:** a verb and a noun in title case, "Create Lead", "Get Task
  Fields", "Request to Join Project".
- **Length:** two or three words.
- **Register:** the title is what the assistant sees in the list of tools,
  so it has to distinguish the tool from its neighbours on its own.

### The tool description

- **Shape:** four labelled parts, in this order: required attributes,
  optional attributes, an example request, and what comes back.
- **Example:** the example is a real call with real arguments, written the
  way the assistant would write it.
- **Note:** the note is only there when the portal refuses something, and
  it says which parameter.

### The argument names

- **Shape:** snake case, `filter_params`, `select_fields`, `project_id`.
- **Structured arguments:** a JSON string, so `filter_params` carries
  `{"STATUS_ID": "NEW"}` and not a nested object.
- **Plain arguments:** an id, a name or a message stay strings.

### The answer

- **Shape:** one JSON document, printed with an indent of two, with the
  characters left as they are.
- **Success:** `{"success": true, ...}` and the fields the tool returns.
- **Failure:** `{"success": false, "error": "..."}`, and the message from
  the portal.

### The list answer

- **Shape:** `success`, then `count`, then the records under the name of
  the entity.
- **Count:** the number of records in the answer, after the limit was
  applied.

## Do's and Don'ts

### Do:

- **Do** keep the four labels in every description, in the same order.
- **Do** give a real example in every description, with the arguments the
  tool takes.
- **Do** name the parameters the portal refuses, in a note.
- **Do** keep the answer a JSON document, with the `success` flag first.
- **Do** pass the portal's own error message back unchanged.

### Don't:

- **Don't** add a key to an answer. An assistant parses it, and a new key
  is a change of the contract.
- **Don't** raise out of a tool. The caller cannot read a traceback, so an
  exception is a lost error message.
- **Don't** translate the portal's field names into the argument naming.
  The two vocabularies belong to different things.
- **Don't** put a second currency, a second entity or a second limit into
  a tool. One call, one question.
- **Don't** soften the wording of an answer. "Task created successfully"
  says what happened.
