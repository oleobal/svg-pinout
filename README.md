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
<img src="./examples/simple.svg" width="100%" height="350">

### Description format

In summary :
 - a list of pins
 - `#`-marked sections identify position (top, bottom, left, right),
   title, alignment mark, and color

I call them "descriptions" and not "code", because they are meant to be
human-readable, close to what you'd write on a piece of paper.
   
Here is the description for the diagram from earlier (`examples/simple.txt`) :
```
# title
Example chip
深圳市电

# bottom
>Status LED (W)
>Status LED (R)

<Clock
# blue
V_SS
V_DD
GND


# top

# no color
<Other sensor
</Sensor
# red
4x <>USB

# left
# mark
```

You can find out the details with the `-d` option or by reading
[this file](format.txt).
A more formal description is available [here](reference.md).

### Usage

As noted earlier, a version is available online.
To run it on your own computer, you'll just need
[Python 3](https://www.python.org/downloads/). It is a command line application.

The command that produced the earlier diagram was :
`python.exe .\pinout.py .\examples\simple.txt .\examples\simple.svg`

That was Windows, obviously.

On Linux (and other Unix systems), it would be closer to :
`python3 pinout.py examples/simple.txt examples/simple.svg`

Help is available with the `-h` option :
`python pinout.py -h`