## SVG-pinout

[This script is available online.](http://tools.richeli.eu/pinout)

This is a very simple script that takes in the description of pins and produces a diagram in SVG format.

In case you are not aware, SVG is :
 - able to be resized losslessly
 - machine-readable, with selectable text
 - very light

This makes it ideal for diagrams !

Here is an example of produced diagram :

<img src="./examples/simple.svg" width="100%" height="300">

### Usage

Needs Python 3 to run. The command that produced the earlier diagram was :

`python .\pinout.py .\examples\simple.txt .\examples\simple.svg`

On Unix-like systems (Linux, etc), it would be :

`./pinout.py examples/simple.txt examples/simple.svg`


Help is available with the `-h` option. The `-d` option details the format for
the text files. In summary :
 - a list of pins, with optional number
 - one can enter a range of pins to avoid repeatedly writing the same names,
   or a repetition
 - `#`-marked sections identify position (top, bottom, left, right),
   alignment mark, and color

 
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
