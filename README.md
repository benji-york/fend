# Fend

Have lots of projects? Want to ensure they all follow the same patterns? Fend can help.

Linters are powerful tools that we should use more.  Fend makes it easy to use pre-built
or custom linters to enforce patterns across all of your projects.  Fend handles the
entire pattern life-cycle from starting slow to integrating new patterns into your
projects.


## Getting started

You can define your own custom patters for Fend to use, but it's easiest to get started
with one of the pre-built patterns.  One of the easiest to start with is
trailing-whitespace.

To see what that pattern thinks about your project, first install Fend.

```shell
pip install fend
```

## Checking files

Now you can run Fend on your project.  Let's start with running it on just one file.

```shell
fend check --enable=trailing-whitespace my_file.py
```

When you run the above, you might see something like this:

```
my_file.py:23 trailing whitespace (trailing-whitespace)
```

This is Fend telling you that it found a pattern violation on line 23 of `my_file.py`, a
message about the violation and which pattern triggered the message.

At this point you might want Fend to tell you what it thinks would fix the violation.
For that use the `--diff` switch.

```shell
fend check --diff --enable=trailing-whitespace my_file.py
```

You will then see the same message as before plus a diff describing what change should
be made to conform to the pattern.

```diff
--- my_file.py
+++ my_file.py
@@ -1,23 +1,23 @@
-This is a line of text. 
+This is a line of text.
?                       ^
```

## Fixing files

Now that you've seen the changes needed to comply with the pattern, you can make those changes or you can let Fend do it for you.

```shell
fend fix --enable=trailing-whitespace my_file.py
```
