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
argparser.add_argument('-d', '--describe-format', dest='describeFormat', action='store_true', help='explain the pinout description format and exit', default=False)
argparser.add_argument('-v', '--verbose', action='store_true', help='print pins to stderr', default=False)
svgTagsGroup = argparser.add_mutually_exclusive_group(required=False)
svgTagsGroup.add_argument('--tags', dest='svgTags', action='store_true', help='include SVG tags around the output (default)')
svgTagsGroup.add_argument('--no-tags', dest='svgTags', action='store_false', help='do not include SVG tags')
argparser.set_defaults(svgTags=True)
argparser.add_argument('infile', help='what file to read a pinout description in', nargs='?', type=argparse.FileType('r'),  default=sys.stdin)
argparser.add_argument('outfile', help='what file to write the SVG output in', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

args = argparser.parse_args()

# originally I overloaded Action, but I couldn't make it work.
if args.describeFormat:
	with open("format.txt", "r") as f:
		print(f.read())
	sys.exit()

pins = {"top":[], "bottom":[], "left":[], "right":[], "default":[]}

marks = []

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
			if words[0].lower() in ("top", "bottom", "left", "right"):
				currentSection = words[0].lower()
			elif words[0].lower() == "mark" :
				marks.append(currentSection)
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
			if currentHighestNumberPlusOne < nbEnd+1:
				currentHighestNumberPlusOne = nbEnd+1
		except ValueError:
		# can't help but feel this organisation is not as elegant as it could be
			try:
				# repetition
				if words[0][-1] != "x":
					raise ValueError("whatever")
				nb = int(words[0][:-1])
				for i in range(nb):
					pins[currentSection].append((currentHighestNumberPlusOne+i, line[len(words[0]):].strip(), currentColor))
				currentHighestNumberPlusOne+=nb
			except ValueError:
				# nothing
				pins[currentSection].append((currentHighestNumberPlusOne, line, currentColor))
				currentHighestNumberPlusOne+=1
			


if args.verbose:
	import pprint
	print(pprint.pformat(pins), file=sys.stderr)
	


fontFamily = "monospace"

# yeah, sucks, doesn't it
# best heuristics
# for the uneducated, this means guesses
charHeight=10
charWidth = 9

widthPerPin = 25
heightPerPin = 22


basex = 10

longestLeftWordLen = 0
for i in pins["left"]:
	if len(i[1]) > longestLeftWordLen:
		longestLeftWordLen = len(i[1])
basex += longestLeftWordLen*charWidth

basey = 10

# a  bit more complicated, because diagonals
# trigonometry, tho
longestUpWordLen = 0
for i in pins["top"]:
	if len(i[1]) > longestUpWordLen:
		longestUpWordLen = len(i[1])

from math import tan, ceil
basey+=ceil(tan(3.14/4)*(longestUpWordLen*charWidth))



# really, I would draw a bounding box and restrict to that, or something.
# but I can't seem to be able to with those tools. It's as if using a
# tools without DOM manipulation is bad for manipulating the DOM


result = ""

pinWidth = max(len(pins["top"]), len(pins["bottom"]))
pinHeight = max(len(pins["left"]), len(pins["right"]))

rectWidth = pinWidth*widthPerPin + (pinWidth//2)
rectHeight = (2+pinHeight)*heightPerPin

result+="<rect x='{}' y='{}' width='{}' height='{}' fill='white' stroke-width='2' stroke='black'/>\n\n".format(basex, basey, rectWidth , rectHeight)

## marks


if "top" in marks:
	startx = basex+(rectWidth//2)-5
	starty = basey
	endx = basex+(rectWidth//2)+5
	endy = basey
	result+="""\
<path d="M{sx} {sy}
		A 5 5 0 0 0 {ex} {ey}"
		stroke="black" fill="black" fill-opacity="0" stroke-width="2"/>

""".format(sx=startx, sy=starty, ex=endx, ey=endy)

if "bottom" in marks:
	startx = basex+(rectWidth//2)-5
	starty = basey+rectHeight
	endx = basex+(rectWidth//2)+5
	endy = basey+rectHeight
	result+="""\
<path d="M{sx} {sy}
		A 5 5 0 0 1 {ex} {ey}"
		stroke="black" fill="black" fill-opacity="0" stroke-width="2"/>

""".format(sx=startx, sy=starty, ex=endx, ey=endy)

if "right" in marks:
	startx = basex+rectWidth
	starty = basey+(rectHeight//2) - 5
	endx = basex+rectWidth
	endy = basey+(rectHeight//2) + 5
	result+="""\
<path d="M{sx} {sy}
		A 5 5 0 0 0 {ex} {ey}"
		stroke="black" fill="black" fill-opacity="0" stroke-width="2"/>

""".format(sx=startx, sy=starty, ex=endx, ey=endy)

if "left" in marks:
	startx = basex
	starty = basey+(rectHeight//2) - 5
	endx = basex
	endy = basey+(rectHeight//2) + 5
	result+="""\
<path d="M{sx} {sy}
		A 5 5 0 0 1 {ex} {ey}"
		stroke="black" fill="black" fill-opacity="0" stroke-width="2"/>

""".format(sx=startx, sy=starty, ex=endx, ey=endy)

## pins 

# yeah I know it's disgusting
# TODO refactor

textLine = "<line x1='{}' y1='{}' x2='{}' y2='{}' stroke='{}' stroke-width='2'/>\n"
textNumber = "<text x='{x}' y='{y}' font-family='{font}' fill='{color}'>{text}</text>\n"
textLabel = "<text x='{x}' y='{y}' transform='rotate({angle} {x} {y})' font-family='{font}' fill='{color}'>{text}</text>\n\n"

i = 0
while i < len(pins["top"]):
	x1 = basex+widthPerPin//2 + i*(widthPerPin)
	y1 = basey
	x2 = x1
	y2 = y1-5
	color = pins["top"][i][2]
	result+=textLine.format(x1,y1,x2,y2, color)
	result+=textNumber.format(x=x1-5, y=y1+12, text=pins["top"][i][0], font=fontFamily, color=color)
	result+=textLabel.format(x=x1,y=y1-5, angle=-45, text=pins["top"][i][1], font=fontFamily, color=color)
	
	i+=1

i=0
while i < len(pins["bottom"]):
	x1 = basex+widthPerPin//2 + i*(widthPerPin)
	y1 = basey+rectHeight
	x2 = x1
	y2 = y1+5
	color = pins["bottom"][i][2]
	result+=textLine.format(x1,y1,x2,y2, color)
	result+=textNumber.format(x=x1-5, y=y1-5, text=pins["bottom"][i][0], font=fontFamily, color=color)
	result+=textLabel.format(x=x1,y=y1+12, angle=45, text=pins["bottom"][i][1], font=fontFamily, color=color)
	
	i+=1

i=0
while i < len(pins["right"]):
	x1 = basex+rectWidth
	y1 = basey+heightPerPin+(heightPerPin//2) + i*heightPerPin
	x2 = x1+5
	y2 = y1
	color = pins["right"][i][2]
	result+=textLine.format(x1,y1,x2,y2, color)
	result+=textNumber.format(x=x1-widthPerPin, y=y1+5, text=pins["right"][i][0], font=fontFamily, color=color)
	result+=textLabel.format(x=x1+6, y=y1+(charHeight//2), angle=0, text=pins["right"][i][1], font=fontFamily, color=color)
	
	i+=1

i=0
while i < len(pins["left"]):
	x1 = basex
	y1 = basey+heightPerPin+(heightPerPin//2) + i*heightPerPin
	x2 = x1-5
	y2 = y1
	color = pins["left"][i][2]
	result+=textLine.format(x1,y1,x2,y2, color)
	result+=textNumber.format(x=x1+6, y=y1+5, text=pins["left"][i][0], font=fontFamily, color=color)
	labelLen = len(pins["left"][i][1])*charWidth
	result+=textLabel.format(x=x1-6-labelLen, y=y1+(charHeight//2), angle=0, text=pins["left"][i][1], font=fontFamily, color=color)
	i+=1


if args.svgTags:
	result = "<svg xmlns='http://www.w3.org/2000/svg' version='1.1'>\n"+result+"\n</svg>\n"

args.outfile.write(result)
