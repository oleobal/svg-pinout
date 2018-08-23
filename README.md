## SVG-pinout

[This tool is available online.](http://tools.richeli.eu/pinout)

This is a simple script that takes in the description of pins and produces
a diagram in SVG format.

In case you were not aware, SVG is :
 - able to be resized losslessly
 - machine-readable, with selectable text
 - very light

This makes it ideal for diagrams !

Here is an example of produced diagram :
<img src="./examples/simple.svg" width="100%" height="300">

### Description format

In summary :
 - a list of pins, with optional number
 - one can enter a range of pins to avoid repeatedly writing the same names,
   or a repetition
 - `#`-marked sections identify position (top, bottom, left, right),
   alignment mark, and color

I call them "descriptions" and not "code", because they are meant to be
human-readable, close to what you'd write on a piece of paper.
   
Here is the description for the diagram from earlier (`examples/simple.txt`) :
```
# Top
1-4 USB
5 Status LED (Write)
6 Status LED (Read)

# Bottom
2x Sensor

Clock
# blue
VSS
VDD
GND

# left
# mark
```

You can find out the details with the `-d` option or by reading
[this file](format.txt).

### Usage

As noted earlier, a version is available online. To run your own, you'll just
needs Python 3.

The command that produced the earlier diagram was :
`python.exe .\pinout.py .\examples\simple.txt .\examples\simple.svg`

That was Windows, obviously.

On Linux (and other Unix systems), it would be closer to :
`python3 pinout.py examples/simple.txt examples/simple.svg`

Help is available with the `-h` option :
`python pinout.py -h`