Reference
=========

This is a precise reference of how the description language behaves.

There are three main categories of lines :
 - Instructions
 - Pin descriptions
 - Comments

Comments are any line that starts with `//` ; they will be ignored.

A fourth category is title sections, explained under `instructions>sections`.

Note that every line is read by first stripping whitespace (spaces, tabs, line
feeds) from its start and end, before any processing is done.

Pin description
---------------

Pin description take the form : `[numbering] <<decoration><pin name>>`.
It is a single line (a new line starts another description).

Here is an example of a description using a lot of features :
`4x <>/V_SS RESET^2 `

### Numbering
Whatever is before the first space is considered numbering, unless it fails
parsing, in which case it is considered part of the decoration + pin name.

It is possible to force a valid numbering expression to be part of the pin name,
by preceding it with a backslash `\`.

Numbering can take the forms :
 - `n`   A single pin number
 - `nx`  A a number followed by the letter `x`. This is immediatly expanded to
   the same pin, `n` times, automatically numbered.
 - `n-k` A range of number, immediatly expanded as identical pins with the 
   numbers n to k (inclusive). If `n>k`, is is expanded by numbering  backwards
   from n.

#### Automatic numbering
When reading the pins, a variable keeps track of the highest pin number so
far, for automatic numbering (no number, or a multiplication).

When a pin number is explicitely given, however, this variable is reset to that.

### Pin decoration

Pin decoration are symbols before the pin name that add visual elements to the
label. There are :
 - `.` Adds a dot after/before the number (typically for identification)
 - `/` Adds a line over the label (typically for active-on-low pins)
 - `>` Adds an outgoing arrow to the pin (typically for output pins)
 - `<` Adds an ingoing arrow to the pin (typically for input pins)

They can be used together and in any order. As soon as a character that is not
one of these is detected, the system considers it is the end of decoration and
the start of the pin name.

### Pin name and formatting

Whatever follows decoration, until the line feed, is the pin name. Pin names
support formatting through :
 - `_` subscripts whatever follows it, until the next space
 - `^` superscripts whatever follows it, until the next space

These can be escaped with backslash `\` (they'll be read as normal characters).


Instructions
------------

Any line that starts with `#` is an instruction, although the `#` can be
escaped with a backslash `\` to be read as a normal character.

The line is stripped of its leading `#`, and converted to lower case ;
it is then inspected in three phases :
 - The line is split on spaces, and checked for multi-word instructions
 - The line is then rejoined, and checked for single-word instructions
 - The line is set as current color
 
### Multi-word instructions

#### Package

The only multi-word instruction is `package`. It can be followed by :
 - `parallel`, or `dip`
 - `qfp`, or `quad`, or `square`, or `carrier`

This tells the program what how the chip is packaged, to command behaviour
when automatically numbering and/or placing pins.

The default packaging is `parallel`.

Words after the second word are ignored.

### Single-word instructions

As explained earlier, the line is converted to lowercase, and joined with
whitespace removed after the multi-word instruction stage. This means, for
example, that `#NOCOLOR` and `# No color` are equivalent.

Single word instructions that effect pins affect all pins following them until
another instruction overrides them.

#### Sections
`top`, `bottom`, `left`, `right`, and `title` will instruct the following pins
they are part of the corresponding section.

`title` is a special section, which hosts not pin descriptions, but text to be
displayed at the center of the chip. Title text discard empty lines, but does
respect line feeds. Text is automatically centered, and turned sideways if the
chip is taller than wide.

There is an additional section, `default`, which hosts pins without a section.
Default has special behaviour, which is explained in `Placement of pins`.

The `side` and `nextside` instructions (synonyms) will automatically place
following pins on whatever side is appropriate. See `Placement of pins`.

Sections can be ended with the `end` and `endsection` instructions.

#### Marks

The `mark` instruction adds a circular alignment mark to the current section.

The `notch` instruction does the same, with a notch onto the left corner of
the section (when looking outwards).

Both also sets the reference side for pin placement (see `Placement of pins`).

It does not affect following pins at all.

#### Endings
`endsection` returns the current section to `default`.

`endcolor` returns the current color whatever it was at the start.

`end` does both at the same time.

`nocolor` is a synonym to `endcolor`.

### Colors

(I have decided to use the american spelling throughough, after much thought.)

Instruction that are not recognized earlier are written as colors for the pins
to follow. Colors are directly copied into SVG ; the set of supported colors
depends on the exact software, but, typically, anything that works in a HTML
file goes. This includes :
 - color names like `black`, `DarkGoldenrod`, `Tomato`
   HTML color names are case-insensitive, which is good since everything is
   lower-cased anyway
 - 6-digits hex like `#FFFFFF`
 - 3-digits hex like `#FFF`

### Instruction chaining

Instructions can be written in the same line by separating them with `;`.

They are executed sequentially, as if they had been written on different lines.



Placement of pins
-----------------

### Ordering

Pins are placed counter-clockwise with respect to a reference side. This means
some pins will be placed right to left or bottom to top.

The reference side is picked depending on number of pin per side : if the chip
is taller than it is wide, it is the top. Else, it is the left side.

The reference side can be overriden with the `mark` (or `notch`)instruction,
in which case it is set to side of the last `mark` (or `notch`) used.

### Automatic sides

#### Automatic side switching (side/nextside)

The `side` or `nextside` instruction will put the following pins in the section
that befits them. Its behavior depends on set packaging : if it is `parallel`
(the default), then `nextside` goes to the side opposite of the current side.
If it is `square`, then `nextside` goes counter-clockwise.

`nextside` when the current section is `title` goes to `default`.

#### Default behavior
The `default` section hosts pins that do have not been placed in another. There
are several cases then :
 - If the `default` section is the only one with pins, then it is divided
   according to the package, putting pins left and right when it is `parallel`
   (the default)
 - Else, it is ignored.

If `nextside` is used while in a `default` section, then `default` is appended to
`left`, and all further additions to `default` will go to `left`. The current
section (for following pins) is then set to `right`.


Considerations
--------------

This is meant to be :
 - Fairly similar to what would intuitively write to describe a pinout
 - Easy to use for electrical engineers and the like

By "easy to use", I of course mean predictable. I am not an EE, so I try to ask
the ones I know what would be the intuitive thing to do in each case, and such.

I also chose `//` as comments because I'd expect most of them to know of it as
C++-style comments (although, really, BCPL).

