#!/usr/bin/python3
"""
produces a SVG file with described pinout

Left and right are not done yet.
Default is not done yet.
Pins above 99 will run into one another.

It would be nice to group pins.
"""
import argparse
import sys

argparser = argparse.ArgumentParser(description="Generates SVG pinouts based on text descriptions (see -d).")
argparser.add_argument('-d', '--describeFormat', action='store_true', help='explain the pinout description format and exit', default=False)
argparser.add_argument('-v', '--verbose', action='store_true', help='print pins to stderr', default=False)
argparser.add_argument('infile', help='what file to read a pinout description in', nargs='?', type=argparse.FileType('r'),  default=sys.stdin)
argparser.add_argument('outfile', help='what file to write the SVG output in', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

args = argparser.parse_args()

# originally I overloaded Action, but I couldn't make it work.
if args.describeFormat:
	print("""\
Formatting :

Four sections : top, bottom, left, right, for where you want the pins to be.
To start a section, write its name with a # in front. Pin descriptions that
follow will belong to that section. Sections can be called multiple times.

Pins can be :
ground pin
1 ground pin
So either a name or a number and a name.

Instead of a number, you can also specify a range, like this :
0-7 I/O
This range is inclusive.
Alternatively, specify a number of pins, like this :
8x I/O
They'll be numbered automatically.

Pins with no number are automatically assigned one.
Pins with no color are black.
Pins with no section are divided between top and bottom, to varying results.

That's right, you can specify color. It works like sections :
# blue
will color everything after it blue.

Empty line and lines starting with # that are more than one word (whitespace
notwithstanding) are ignored. To provide for a sure way of writing comments,
line starting with ## are always ignored.
""")
	sys.exit()

pins = {"top":[], "bottom":[], "left":[], "right":[], "default":[]}

currentSection="default"
currentHighestNumberPlusOne=0
currentColor="black"
for line in args.infile:
	line = line.strip()
	if line == "":
		continue
	if line[0] == "#":
		if len(line) == 1:
			continue
		if line[1] == "#":
			continue
		words = line[1:].split()
		if len(words) == 1 :
			if words[0] in ("top", "bottom", "left", "right"):
				currentSection = words[0]
			else:
				currentColor = words[0]
		continue
	
	words = line.split()
	try:
		# pin number
		nb = int(words[0])
		if currentHighestNumberPlusOne < nb+1:
			currentHighestNumberPlusOne = nb+1
		pins[currentSection].append((nb, line[len(words[0]):].strip(), currentColor))
	except ValueError:
		try:
			# range
			nbs = words[0].split("-")
			nbStart = int(nbs[0])
			nbEnd = int(nbs[-1])
			for n in range(nbStart, nbEnd+1):
				pins[currentSection].append((n, line[len(words[0]):].strip(), currentColor))
			if currentHighestNumberPlusOne < nbEnd+2:
				currentHighestNumberPlusOne = nbEnd+2
		except ValueError:
		# can't help but feel this organisation is not as elegant as it could be
			try:
				# repetition
				if words[0][-1] != "x":
					raise ValueError("whatever")
				nb = int(words[0][:-1])
				for i in range(nb):
					pins[currentSection].append((currentHighestNumberPlusOne+i, line[len(words[0]):].strip(), currentColor))
				currentHighestNumberPlusOne+=i+1
			except ValueError:
				# nothing
				pins[currentSection].append((currentHighestNumberPlusOne, line, currentColor))
				currentHighestNumberPlusOne+=1
			


if args.verbose:
	import pprint
	print(pprint.pformat(pins), file=sys.stderr)
	


fontFamily = "monospace"

widthPerPin = 25
heightPerPin = 15

basex = 50
basey = 150

result = ""

pinWidth = max(len(pins["top"]), len(pins["bottom"]))
pinHeight = max(len(pins["left"]), len(pins["right"]))

rectWidth = pinWidth*widthPerPin
rectHeight = (3+pinHeight)*heightPerPin

result+="<rect x='{}' y='{}' width='{}' height='{}' fill='white' stroke-width='2' stroke='black'/>\n".format(basex, basey, rectWidth , rectHeight)

# yeah I know it's disgusting
# TODO refactor

i = 0
while i < len(pins["top"]):
	x1 = basex+widthPerPin//2 + i*(widthPerPin)
	y1 = basey
	x2 = x1
	y2 = y1-5
	color = pins["top"][i][2]
	result+="<line x1='{}' y1='{}' x2='{}' y2='{}' stroke='{}' stroke-width='2'/>\n".format(x1,y1,x1,y2, color)
	result+="<text x='{x}' y='{y}' font-family='{font}' fill='{color}'>{text}</text>\n".format(x=x1-5, y=y1+12, text=pins["top"][i][0], font=fontFamily, color=color)
	result+="<text x='{x}' y='{y}' transform='rotate(-45 {x} {y})' font-family='{font}' fill='{color}'>{text}</text>\n\n".format(x=x1,y=y1-5, text=pins["top"][i][1], font=fontFamily, color=color)
	
	i+=1

i=0
while i < len(pins["bottom"]):
	x1 = basex+widthPerPin//2 + i*(widthPerPin)
	y1 = basey+rectHeight
	x2 = x1
	y2 = y1+5
	color = pins["bottom"][i][2]
	result+="<line x1='{}' y1='{}' x2='{}' y2='{}' stroke='{}' stroke-width='2'/>\n".format(x1,y1,x1,y2, color)
	result+="<text x='{x}' y='{y}' font-family='{font}' fill='{color}'>{text}</text>\n".format(x=x1-5, y=y1-5, text=pins["bottom"][i][0], font=fontFamily, color=color)
	result+="<text x='{x}' y='{y}' transform='rotate(45 {x} {y})' font-family='{font}' fill='{color}'>{text}</text>\n\n".format(x=x1,y=y1+12, text=pins["bottom"][i][1], font=fontFamily, color=color)
	
	i+=1

result = "<svg xmlns='http://www.w3.org/2000/svg' version='1.1'>\n"+result+"\n</svg>\n"

args.outfile.write(result)
