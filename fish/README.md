# Fish shell

A practical path from casual interactive use to confident Fish scripting.

This guide assumes you already use Fish as your normal shell, know basic Unix commands, have written a few Fish functions, and have occasionally used `for` loops. The goal is not to teach shell basics from scratch. It is to make Fish itself feel like a language and tool you can deliberately leverage.

Current Fish documentation: https://fishshell.com/docs/current/

---

## 1. Mental model: Fish is not Bash with nicer syntax

The most important step is to stop translating Bash idioms mechanically.

Fish deliberately differs from POSIX shells in several areas:

- variables are lists by default;
- `set` handles assignment, scoping, exporting, and erasing;
- command substitution uses `(...)` or `$(...)`;
- unquoted variables do **not** undergo Bash-style word splitting;
- functions use `$argv`, or named arguments via `--argument-names`;
- control flow is command-oriented: `if`, `for`, `while`, `switch`, `begin`, `end`;
- many things that Bash expresses with punctuation are ordinary Fish commands.

A good Fish script should usually look like Fish, not like translated Bash.

---

## 2. Variables: learn `set` properly

Basic assignment:

```fish
set name Max
```

Multiple values produce a list:

```fish
set dirs ~/Downloads ~/Desktop ~/Documents
```

Now `$dirs` expands to three arguments:

```fish
printf '%s\n' $dirs
```

This is one of the most important differences from Bash. Fish variables naturally represent argument lists.

### Scope

Fish has several scopes:

```fish
set -l local_var value      # local to current block
set -f function_var value   # current function
set -g global_var value     # current Fish process
set -U universal_var value  # persistent across Fish sessions
```

Export a variable:

```fish
set -x API_ENV development
```

Combine scope and export:

```fish
set -gx EDITOR nvim
```

Erase a variable:

```fish
set -e EDITOR
```

### Practical rule

Inside scripts and functions, prefer local variables unless there is a reason not to:

```fish
set -l root ~/Downloads
```

Avoid casually using universal variables for configuration you might later want under source control. Universal variables persist outside your config files, which can make configuration harder to inspect.

### Lists and indexing

Fish indexing is 1-based:

```fish
set fruits apple banana pear

echo $fruits[1]   # apple
echo $fruits[-1]  # pear
```

Slices:

```fish
echo $fruits[1..2]
```

A useful habit is to think of Fish variables as arrays first and strings second.

---

## 3. Quoting and expansion

Single quotes suppress Fish expansion:

```fish
echo '$HOME'
```

Double quotes allow variable expansion and `$(...)` command substitution:

```fish
echo "Home: $HOME"
echo "Current branch: $(git branch --show-current)"
```

Unquoted list variables expand into multiple arguments:

```fish
set files one.txt two.txt
rm $files
```

Quoted list variables become a single argument:

```fish
printf '%s\n' "$files"
```

Fish does not perform Bash-style post-expansion whitespace splitting. This means this is safe:

```fish
set filename 'My File.txt'
rm $filename
```

Fish passes one argument to `rm`.

This is a major reason Fish scripting is often less quote-heavy and less fragile than POSIX shell scripting.

---

## 4. Command substitution

Classic Fish syntax:

```fish
set branch (git branch --show-current)
```

Modern Fish also supports:

```fish
set branch $(git branch --show-current)
```

A command substitution generally splits output on newlines, not arbitrary whitespace.

Example:

```fish
set files (find . -name '*.ts')
```

Each output line becomes a list element.

If a command emits space-separated fields that you deliberately want split, do it explicitly:

```fish
set flags (pkg-config --libs gio-2.0 | string split ' ')
```

That explicitness is a recurring Fish pattern: avoid implicit text splitting when you can represent the structure directly.

---

## 5. Stop parsing text when Fish already has a primitive

A common shell-scripting failure mode is reaching for `grep`, `sed`, `awk`, or `cut` for tasks the shell can already express.

Fish has strong builtins for common scripting work:

- `string`
- `path`
- `math`
- `test`
- `contains`
- `count`
- `read`
- `argparse`

Examples:

```fish
string upper hello
```

```fish
string replace '.json' '.yaml' config.json
```

```fish
path basename ~/Downloads/example.txt
```

```fish
math '12 * 4 + 3'
```

```fish
contains foo foo bar baz
```

```fish
count $argv
```

Before constructing a pipeline, check whether one of these builtins already does the job.

---

## 6. Conditionals

Fish conditionals run commands and inspect their exit status.

```fish
if test -e config.json
    echo found it
end
```

Or more naturally with a command whose status already conveys the condition:

```fish
if git diff --quiet
    echo clean
else
    echo dirty
end
```

Fish also supports `&&` and `||`:

```fish
mkdir build && cd build
```

And the older Fish combiners `and` / `or` still appear in Fish code:

```fish
command -q rg; and echo 'ripgrep installed'
```

For new code, `&&` and `||` are usually easier to read.

### `test`

Common patterns:

```fish
test -e file.txt       # exists
test -f file.txt       # regular file
test -d directory      # directory
test -n "$name"        # non-empty string
test "$a" = "$b"      # string equality
test $count -gt 10     # numeric comparison
```

For string matching, `string match` is often clearer than complex `test` expressions.

---

## 7. Loops

You already use basic `for` loops. The important improvement is to loop over structured Fish lists instead of parsing `ls` output.

Avoid:

```fish
for file in (ls ~/Downloads)
    echo $file
end
```

Prefer glob expansion:

```fish
for file in ~/Downloads/*
    echo $file
end
```

Now each pathname remains a proper argument, including filenames containing spaces.

### Loop over command output

```fish
for branch in (git branch --format='%(refname:short)')
    echo $branch
end
```

### While loops

```fish
set -l i 1
while test $i -le 5
    echo $i
    set i (math $i + 1)
end
```

### Reading a file line by line

```fish
while read -l line
    echo "line: $line"
end < input.txt
```

---

## 8. Functions

Basic function:

```fish
function mkcd
    mkdir -p $argv[1]
    and cd $argv[1]
end
```

Arguments are available through `$argv`:

```fish
function showargs
    printf '%s\n' $argv
end
```

Named arguments can make functions much easier to understand:

```fish
function backup --argument-names source destination
    cp -R $source $destination
end
```

Fish still leaves the arguments in `$argv`, but assigns successive arguments to the named variables.

### Function descriptions

```fish
function mkcd --description 'Create a directory and enter it'
    mkdir -p $argv[1]
    and cd $argv[1]
end
```

Descriptions integrate with Fish's interactive help/completion ecosystem.

### Wrapping commands

If your function wraps another command, tell Fish:

```fish
function g --wraps git
    git $argv
end
```

Fish can then inherit Git completions for `g`.

### Persistence

Interactive functions are commonly stored as:

```text
~/.config/fish/functions/function_name.fish
```

The filename should match the function name.

Fish can also save an interactively defined function:

```fish
funcsave my_function
```

---

## 9. `argparse`: write real command-line interfaces

For anything more complex than positional arguments, learn Fish's `argparse` builtin.

Example:

```fish
function deploy
    argparse 'e/environment=' 'n/dry-run' -- $argv
    or return

    if set -q _flag_environment
        set -l env $_flag_environment
    else
        set -l env staging
    end

    if set -q _flag_dry_run
        echo "Would deploy to $env"
        return
    end

    echo "Deploying to $env"
end
```

Usage:

```fish
deploy --environment production --dry-run
```

This is much better than manually iterating over `$argv` once your function starts behaving like a small CLI program.

---

## 10. Exit statuses and `$status`

Every command returns an exit status.

Immediately after a command:

```fish
git diff --quiet
set -l result $status
```

Conventionally:

- `0` means success;
- non-zero means failure or some other condition.

Fish conditionals use this directly:

```fish
if command -q ffmpeg
    echo installed
end
```

For pipelines, Fish exposes `$pipestatus`:

```fish
cat data.txt | grep foo | sort
printf '%s\n' $pipestatus
```

This gives the status of every command in the pipeline.

A robust function should often return a meaningful status:

```fish
function require_command --argument-names cmd
    if not command -q $cmd
        echo "Missing command: $cmd" >&2
        return 1
    end
end
```

---

## 11. Redirection and pipelines

Standard redirection:

```fish
command > output.txt
command >> output.txt
command < input.txt
command 2> errors.txt
```

Redirect stderr to stdout:

```fish
command 2>&1
```

Fish's pipelines work normally:

```fish
rg TODO src | sort | uniq
```

But do not overuse pipelines simply because shell makes them convenient. If the data is already a Fish list, `string`, `path`, or a loop may be easier to reason about.

---

## 12. `begin ... end`: grouping commands

`begin` creates a command block without introducing a loop or conditional.

Useful for grouped redirection:

```fish
begin
    echo 'stdout-like information'
    echo 'more information'
end > report.txt
```

It also gives you a local scope boundary:

```fish
begin
    set -l temporary value
    echo $temporary
end

# $temporary no longer exists here
```

---

## 13. `switch`

For discrete cases, `switch` is cleaner than a long `if` chain.

```fish
switch $argv[1]
    case start
        echo starting
    case stop
        echo stopping
    case restart
        echo restarting
    case '*'
        echo 'usage: service {start|stop|restart}'
        return 1
end
```

Fish cases do not fall through.

---

## 14. Globs and path handling

Fish supports ordinary wildcards:

```fish
*.jpg
src/**/*.ts
```

But for nontrivial path manipulation, learn the `path` builtin.

Examples:

```fish
path basename /tmp/foo/bar.txt
# bar.txt
```

```fish
path dirname /tmp/foo/bar.txt
# /tmp/foo
```

```fish
path extension file.tar.gz
```

```fish
path resolve ./foo/../bar
```

For scripts involving files, using `path` usually produces clearer code than manually splitting on `/`.

---

## 15. `string`: one of Fish's most useful tools

Become comfortable with these subcommands:

```text
string split
string join
string match
string replace
string trim
string lower
string upper
string escape
string collect
```

Examples:

```fish
set parts (string split ':' $PATH)
```

```fish
string match -r '^feature/' $branch
```

```fish
set slug (string lower $name | string replace -a ' ' '-')
```

```fish
string trim (cat value.txt)
```

A large portion of practical shell scripting is transforming strings. Fish's `string` builtin should be one of your default tools.

---

## 16. `command`, `builtin`, and function shadowing

Fish functions can shadow external commands.

Suppose you define:

```fish
function ls
    echo custom
end
```

Then:

```fish
ls
```

runs your function.

To explicitly run the external command:

```fish
command ls
```

To explicitly invoke a Fish builtin:

```fish
builtin read
```

This matters when writing wrappers:

```fish
function rm --wraps rm
    command rm -i $argv
end
```

Without `command`, the function would recursively call itself.

---

## 17. Discoverability: `type`, `functions`, `command -q`

Find out what a command name resolves to:

```fish
type ls
```

Show a function definition:

```fish
functions mkcd
```

Check whether a command exists without printing anything:

```fish
command -q rg
```

This is useful in configuration:

```fish
if command -q zoxide
    zoxide init fish | source
end
```

---

## 18. Fish configuration structure

The central configuration file is:

```text
~/.config/fish/config.fish
```

Do not put every function in that file.

A clean configuration often looks like:

```text
~/.config/fish/
├── config.fish
├── conf.d/
│   ├── environment.fish
│   └── tools.fish
├── functions/
│   ├── mkcd.fish
│   ├── extract.fish
│   └── fish_prompt.fish
└── completions/
    └── mytool.fish
```

Use `config.fish` for small startup configuration.

Use `conf.d/*.fish` for modular startup configuration.

Use `functions/*.fish` for autoloaded functions.

Use `completions/*.fish` for custom command completions.

This structure scales much better than a monolithic config file.

---

## 19. Interactive power-user features worth learning

Fish's scripting language is only half the value. Its interactive editing model is unusually capable.

### Autosuggestions

Fish learns from your history and offers suggestions inline. Rather than retyping long commands, learn to accept partial or complete suggestions efficiently.

### Searchable history

Typing part of a command and navigating history searches for matching commands. This is more useful when you deliberately type a distinctive substring first.

### Tab completion

Fish completions are context-aware and often include descriptions.

Try pressing Tab aggressively on unfamiliar commands. Fish often exposes options, Git branches, process names, paths, and command-specific values.

### Abbreviations

Abbreviations are often better than aliases for interactive use because they expand visibly before execution.

```fish
abbr -a gst 'git status'
```

Typing `gst` expands into `git status` on the command line.

This means your history contains the real command, and you can edit it before running it.

Use aliases/functions when behavior should remain abstracted. Use abbreviations when the goal is mainly typing less.

---

## 20. Custom completions

You can define completions for your own scripts and functions.

Example:

```fish
complete -c deploy -l environment -s e -r -a 'staging production'
complete -c deploy -l dry-run -s n
```

Now Fish understands:

```text
deploy --environment <TAB>
```

and can suggest `staging` or `production`.

For frequently used personal tooling, custom completion is one of the highest-leverage Fish features.

---

## 21. Events and hooks

Fish functions can respond to events.

Example: run when a variable changes:

```fish
function on_pwd_change --on-variable PWD
    echo "Now in $PWD"
end
```

Other event mechanisms include process events, signals, and generic emitted events.

These are useful for shell customization, though they should be used sparingly in ordinary scripts because hidden event-driven behavior can make configuration harder to understand.

---

## 22. Writing standalone Fish scripts

A Fish script can start with:

```fish
#!/usr/bin/env fish
```

Example:

```fish
#!/usr/bin/env fish

function usage
    echo 'usage: rename-ext OLD NEW FILE...'
end

if test (count $argv) -lt 3
    usage >&2
    exit 1
end

set -l old $argv[1]
set -l new $argv[2]

for file in $argv[3..-1]
    set -l stem (string replace -r "\\.$old\$" '' $file)

    if test $stem = $file
        echo "Skipping $file: does not end in .$old" >&2
        continue
    end

    mv -- $file "$stem.$new"
end
```

Then:

```sh
chmod +x rename-ext.fish
./rename-ext.fish jpg png *.jpg
```

### When Fish scripts are appropriate

Fish is excellent for:

- your own automation;
- workstation tooling;
- developer utilities;
- scripts intended for environments where Fish is known to exist.

Fish is less appropriate when you need a script to run on arbitrary Unix systems without installing anything. For that, POSIX `sh` is more portable.

---

## 23. Error handling patterns

Shell scripting does not have exceptions in the usual programming-language sense. Robustness comes from checking statuses and returning early.

Example:

```fish
function publish
    npm test
    or return

    npm run build
    or return

    npm publish
end
```

Equivalent explicit form:

```fish
function publish
    if not npm test
        return 1
    end

    if not npm run build
        return 1
    end

    npm publish
end
```

For meaningful errors:

```fish
if not test -f package.json
    echo 'package.json not found' >&2
    return 1
end
```

A good shell script should fail near the actual problem instead of continuing with invalid assumptions.

---

## 24. Debugging Fish scripts

### Print commands as they execute

Fish has tracing support:

```fish
fish_trace=1 fish script.fish
```

Or inside Fish:

```fish
set -lx fish_trace 1
source script.fish
```

### Syntax-check a script

```fish
fish --no-execute script.fish
```

This parses the script without executing it.

### Inspect resolution

If a command behaves unexpectedly:

```fish
type command_name
```

This tells you whether Fish is executing a function, builtin, or external command.

### Inspect variables

```fish
set --show VARIABLE
```

This is particularly useful because it displays scope, export status, and values.

---

## 25. Common anti-patterns to unlearn

### Parsing `ls`

Avoid:

```fish
for f in (ls *.txt)
```

Use:

```fish
for f in *.txt
```

### Treating variables as scalar strings by default

Instead of building a command string:

```fish
set args '--verbose --force'
mytool $args
```

Represent arguments structurally:

```fish
set args --verbose --force
mytool $args
```

### Using `eval` unnecessarily

If you find yourself constructing a giant command string and evaluating it, reconsider whether you can build a Fish list of arguments instead.

### Overusing universal variables

Use `set -U` for genuinely persistent interactive settings, not as a substitute for organized configuration files.

### Writing Bash syntax in Fish

Fish intentionally rejects many Bash forms. Do not fight that. Learn the native Fish primitive instead.

---

## 26. A practical progression

The fastest way to become proficient is not to memorize every Fish feature. Build progressively more capable personal tooling.

### Stage 1 — interactive fluency

Become comfortable with:

- abbreviations;
- autosuggestions;
- history search;
- completions;
- `type`;
- `command -q`;
- `string`;
- `path`.

### Stage 2 — functions

Rewrite your frequently repeated shell sequences as functions.

Practice:

- `$argv`;
- named arguments;
- local variables;
- `return`;
- exit-status handling;
- `--wraps`;
- autoloading from `functions/`.

### Stage 3 — small scripts

Write utilities around real work:

- batch file conversion;
- Git helpers;
- project setup;
- deployment helpers;
- log filtering;
- development environment startup.

Add:

- `argparse`;
- validation;
- usage messages;
- meaningful exit statuses.

### Stage 4 — shell integration

Learn:

- custom completions;
- `conf.d`;
- event handlers;
- prompt functions;
- commandline manipulation.

At this point Fish stops being merely your shell and becomes a programmable interface to your development environment.

---

## 27. Exercises

These are deliberately practical rather than academic.

### Exercise 1 — safer batch processing

Write a function:

```text
foreach-file EXT COMMAND...
```

that runs a command on every file in the current directory matching an extension.

Requirements:

- filenames with spaces must work;
- return non-zero if any invocation fails;
- do not parse `ls`.

### Exercise 2 — project navigation

Write a `cproj` function that:

1. searches a known projects directory;
2. accepts a partial project name;
3. changes into the matching project;
4. prints a useful error if no match exists;
5. provides tab completion for project names.

### Exercise 3 — Git helper

Write `gclean` that:

1. checks whether the current directory is a Git repository;
2. lists branches merged into the current branch;
3. excludes protected names such as `main` and `master`;
4. asks before deleting anything.

### Exercise 4 — CLI options

Write a function that uses `argparse`:

```text
backup --source DIR --destination DIR [--dry-run]
```

Validate both directories and return meaningful errors.

### Exercise 5 — developer environment launcher

Write a `dev` function that accepts a project name and then:

- enters its directory;
- starts or attaches to a `tmux` session;
- optionally launches an editor;
- optionally runs a startup command;
- offers Fish completions for known project names.

This exercise combines most of the Fish features worth mastering.

---

## 28. Things worth memorizing

You do not need to memorize the whole language. These primitives cover a large percentage of practical Fish scripting:

```text
set
set -l
set -q
set -e
$argv
$status
$pipestatus
if / else / end
for / while / end
switch / case / end
begin / end
function / end
return
and / or / not
&& / ||
test
string
path
math
read
count
contains
argparse
command
command -q
type
functions
complete
abbr
```

If these become automatic, the rest of Fish is mostly discoverable as needed.

---

## 29. Reference habits

Fish's built-in documentation is unusually useful.

Try:

```fish
help set
```

```fish
help string
```

```fish
help argparse
```

```fish
man fish
```

And remember that Fish's web documentation is divided usefully into:

- Tutorial — quick introduction and idioms;
- Fish language — comprehensive scripting-language reference;
- Interactive use — command-line editing and shell behavior;
- individual command pages — detailed builtin documentation.

Official documentation:

- https://fishshell.com/docs/current/tutorial.html
- https://fishshell.com/docs/current/language.html
- https://fishshell.com/docs/current/interactive.html
- https://fishshell.com/docs/current/commands.html

---

## 30. Target level

You should consider yourself comfortable with Fish when you can look at a repeated shell workflow and naturally decide among:

- a one-liner;
- an abbreviation;
- a function;
- a standalone Fish script;
- a custom completion;
- a small configuration hook.

The key skill is not knowing every Fish feature. It is recognizing when Fish already has a structured primitive for something you would otherwise solve with fragile text manipulation or repeated manual commands.
