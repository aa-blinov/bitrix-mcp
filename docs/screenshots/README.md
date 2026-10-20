# Screenshots

The repository holds no images, and there is nothing here to show.

The server is a process. It has no window, no page and no console art: it
speaks the Model Context Protocol over stdio, and everything a person sees
belongs to the assistant that called it. A picture of the server would be a
picture of somebody else's window.

There is no screenshot of the portal either. The portal is Bitrix24's, the
server only calls it, and a picture of it would show the product of another
company.

## The closest thing to a picture

`test_real_api.py` prints what it finds when it walks a live portal. Its
output shows the whole interface on one screen: the configuration it
loaded, the project it found, the task it created, the update it made and
the leads it listed.

```bash
PYTHONPATH=src python test_real_api.py
```

It needs credentials in `.env`, and it creates a task in a project called
"test" while it runs.

## What would be worth adding

A picture of the assistant calling one of the tools, with the tool
description and the answer side by side. That would show the contract the
whole repository is built around, which no screenshot of this project can
show on its own.

Until there is one, this file stays empty of images, and the README links
to nothing.
