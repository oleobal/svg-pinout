#!/usr/bin/python3
"""
produces a SVG file with described pinout

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
argparser.add_argument('-b', '--background', type=str, help='use this background color (default: none)', default=None)
"""
Background is a rectangle of width/height=100% with class='pinout-bg-rect'
"""
argparser.add_argument('-f', '--foreground', type=str, help='use this foreground color (default: black)', default="black")
argparser.add_argument('-l', '--lighten', action='store_true', help='automatically lighten colors')
"""
Stupid method (overlaying with a transparent white element)
Only used on pins and their labels
Skipped if already white
Given class='pinout-lighten-overlay' for easier stripping
"""
argparser.add_argument('infile', help='what file to read a pinout description in', nargs='?', type=argparse.FileType('r'),  default=sys.stdin)
argparser.add_argument('outfile', help='what file to write the SVG output in', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

args = argparser.parse_args()

# originally I overloaded Action, but I couldn't make it work.
if args.describeFormat:
	with open("format.txt", "r") as f:
		print(f.read())
	sys.exit()

pins = {"top":[], "bottom":[], "left":[], "right":[]}

marks = []

strokeColor = args.foreground

title={"text":[],
	"width":0,
	"height":0,
	"angle":0}

if args.background is not None :
	bgColor = args.background
else:
	bgColor = "none"

def processWord(word):
	"""
	to manage not, arrows, indices..
	returns (processed text, list of features as strings)
	"""
	features = []
	
	leadingSymbols = ["/"]
	
	while word[0] in leadingSymbols:
		sym = word[0]
		word = word[1:]
		
		if sym == "/":
			features.append("not")
		elif sym == ">":
			features.append("arrow-out")
		elif sym == "<":
			features.append("arrow-in")
			
	return (word, features)

currentSection="top"
currentHighestNumberPlusOne=0
currentColor=strokeColor
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
			if words[0].lower() in ("top", "bottom", "left", "right", "title"):
				currentSection = words[0].lower()
			elif words[0].lower() == "mark" :
				marks.append(currentSection)
			elif words[0].lower() == "nocolor" :
				currentColor = strokeColor
			else:
				currentColor = words[0]
		continue
	
	if currentSection == "title":
		if line != "":
			title["text"].append(line)
		continue
	
	words = line.split()
	
	try:
		# pin number
		nb = int(words[0])
		if currentHighestNumberPlusOne < nb+1:
			currentHighestNumberPlusOne = nb+1
		p = processWord(line[len(words[0]):].strip())
		pins[currentSection].append((nb, p[0], currentColor, p[1]))
	except ValueError:
		try:
			# range
			nbs = words[0].split("-")
			nbStart = int(nbs[0])
			nbEnd = int(nbs[-1])
			if nbStart < nbEnd : # forwards range
				p = processWord(line[len(words[0]):].strip())
				for n in range(nbStart, nbEnd+1):
					pins[currentSection].append((n, p[0], currentColor, p[1]))
				if currentHighestNumberPlusOne < nbEnd+1:
					currentHighestNumberPlusOne = nbEnd+1
			else: # backwards range
				nbStart, nbEnd = nbEnd, nbStart
				p = processWord(line[len(words[0]):].strip())
				for n in reversed(range(nbStart, nbEnd+1)):
					pins[currentSection].append((n, p[0], currentColor, p[1]))
				if currentHighestNumberPlusOne < nbEnd+1:
					currentHighestNumberPlusOne = nbEnd+1
				
		except ValueError:
		# can't help but feel this organisation is not as elegant as it could be
			try:
				# repetition
				if words[0][-1] != "x":
					raise ValueError("whatever")
				nb = int(words[0][:-1])
				p = processWord(line[len(words[0]):].strip())
				for i in range(nb):
					pins[currentSection].append((currentHighestNumberPlusOne+i, p[0], currentColor, p[1]))
				currentHighestNumberPlusOne+=nb
			except ValueError:
				# nothing
				p = processWord(line)
				pins[currentSection].append((currentHighestNumberPlusOne, p[0], currentColor, p[1]))
				currentHighestNumberPlusOne+=1
			


if args.verbose:
	import pprint
	print("== TITLE ==", file=sys.stderr)
	print(pprint.pformat(title), file=sys.stderr)
	print("== MARKS ==", file=sys.stderr)
	print(marks, file=sys.stderr)
	print("== PINS  ==", file=sys.stderr)
	print(pprint.pformat(pins), file=sys.stderr)
	
 
fontFamily = "monospace"

# yeah, sucks, doesn't it
# best heuristics
# for the uneducated, this means guesses

# on MS EDge I measured 10 pt height letters
# with 15pt em
charHeight=15
charWidth = 8

widthPerPin = 25
heightPerPin = 22


basex = 20

longestLeftWordLen = 0
for i in pins["left"]:
	if len(i[1]) > longestLeftWordLen:
		longestLeftWordLen = len(i[1])
basex += longestLeftWordLen*charWidth

basey = 20

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

rectWidth  = pinWidth*widthPerPin
rectHeight = pinHeight*heightPerPin

if len(pins["top"]) > 0 :
	rectHeight+=heightPerPin
if len(pins["bottom"]) > 0 :
	rectHeight+=heightPerPin
if len(pins["left"]) > 0 and max(len(pins["top"]), len(pins["bottom"])) == 0 :
	rectWidth +=widthPerPin
if len(pins["right"]) > 0 and max(len(pins["top"]), len(pins["bottom"])) == 0 :
	rectWidth +=widthPerPin

for i in title["text"]:
	if len(i)*charWidth > title["width"]:
		title["width"] = len(i)*charWidth
title["height"] = charHeight*(len(title["text"]))

if rectHeight > rectWidth:
	title["angle"] = -90
	rectWidth+=title["height"]
else:
	title["angle"] = 0
	rectHeight+=title["height"]

result+="<rect x='{}' y='{}' width='{}' height='{}' fill='{}' stroke-width='2' stroke='{}'/>\n\n".format(basex, basey, rectWidth , rectHeight, bgColor, strokeColor)


## title

if len(title["text"]) > 0 :
	titlex = basex+rectWidth//2
	titley = basey+rectHeight//2
	result+="<text x='{x}' y='{y}' transform='rotate({angle} {x} {y})' alignment-baseline='central' text-anchor='middle' font-family='{font}'>\n".format(x=titlex, y=titley, angle=title["angle"], font=fontFamily)
	alignDelta = 0
	if title["angle"] == 0:
		alignDelta = +0.3
	# the -0.3 is heuristics. On most fonts, the characters proper
	# are only the bottom 2/3 of the em.
	result+="\t<tspan x='{x}' dy='{dy}em'>{text}</tspan>\n".format(x=titlex, dy=-(len(title["text"])/2-1+alignDelta), text=title["text"][0])
	for i in range(1,len(title["text"])):
		result+="\t<tspan x='{x}' dy='1em'>{text}</tspan>\n".format(x=titlex, text=title["text"][i])
	result+="</text>\n\n"


## marks


if "top" in marks:
	startx = basex+(rectWidth//2)-5
	starty = basey
	endx = basex+(rectWidth//2)+5
	endy = basey
	result+="""\
<path d="M{sx} {sy}
		A 5 5 0 0 0 {ex} {ey}"
		stroke="{color}" fill="{color}" fill-opacity="0" stroke-width="2"/>

""".format(sx=startx, sy=starty, ex=endx, ey=endy,color=strokeColor)

if "bottom" in marks:
	startx = basex+(rectWidth//2)-5
	starty = basey+rectHeight
	endx = basex+(rectWidth//2)+5
	endy = basey+rectHeight
	result+="""\
<path d="M{sx} {sy}
		A 5 5 0 0 1 {ex} {ey}"
		stroke="{color}" fill="{color}" fill-opacity="0" stroke-width="2"/>

""".format(sx=startx, sy=starty, ex=endx, ey=endy, color=strokeColor)

if "right" in marks:
	startx = basex+rectWidth
	starty = basey+(rectHeight//2) - 5
	endx = basex+rectWidth
	endy = basey+(rectHeight//2) + 5
	result+="""\
<path d="M{sx} {sy}
		A 5 5 0 0 0 {ex} {ey}"
		stroke="{color}" fill="{color}" fill-opacity="0" stroke-width="2"/>

""".format(sx=startx, sy=starty, ex=endx, ey=endy, color=strokeColor)

if "left" in marks:
	startx = basex
	starty = basey+(rectHeight//2) - 5
	endx = basex
	endy = basey+(rectHeight//2) + 5
	result+="""\
<path d="M{sx} {sy}
		A 5 5 0 0 1 {ex} {ey}"
		stroke="{color}" fill="{color}" fill-opacity="0" stroke-width="2"/>

""".format(sx=startx, sy=starty, ex=endx, ey=endy, color=strokeColor)

## pins 

# yeah I know it's disgusting
# TODO refactor

textLine = "<line x1='{}' y1='{}' x2='{}' y2='{}' stroke='{}' stroke-width='2' {add}/>\n"
textNumber = "<text x='{x}' y='{y}' font-family='{font}' fill='{color}' {add}>{text}</text>\n"
textLabel = "<text x='{x}' y='{y}' transform='rotate({angle} {x} {y})' font-family='{font}' fill='{color}' {add}>{text}</text>\n\n"


def labelPinCommon(pin, color=None):
	"""
		if color is set, it will be used instead of the pin color
	"""
	global textLabel
	global fontFamily
	
	if color is None:
		color = pin[2]
	
	toAdd=""
	if "not" in pin[3]:
		toAdd+="style='text-decoration: overline'"
	
	p = pin[1]
	text = ""
	
	i = 0
	while i < len(pin[1]):
		if p[i] in ("_", "^"):
			if p[i] == "_" :
				text+="<tspan dy='5'>"
			elif p[i] == "^":
				text+="<tspan dy='-5'>"
			i+=1
			while i < len(pin[1]) and p[i] != " ":
				if p[i] == "\\":
					i+=1
					text+=p[i]
				else:
					text+=p[i]
				i+=1
			text+="</tspan>"
		elif p[i] == "\\":
			i+=1
			text+=p[i]
		else:
			text+=p[i]
			
		i+=1
	
	t = textLabel.format(x="{x}", y="{y}", angle="{angle}", text=text, font=fontFamily, color=color, add=toAdd+" {add}")
	
	return t

def getPinsTop(pins, font, add="", forceColor=None):
	i = 0
	result=""
	while i < len(pins["top"]):
		x1 = basex+widthPerPin//2 + i*(widthPerPin)
		y1 = basey
		x2 = x1
		y2 = y1-5
		if forceColor is not None:
			color=forceColor
		else:
			color = pins["top"][i][2]
		
		result+=textLine.format(x1,y1,x2,y2, color, add=add)
		result+=textNumber.format(x=x1-5, y=y1+12, text=pins["top"][i][0], font=font, color=color, add=add)
		result+=labelPinCommon(pins["top"][i], color=color).format(x=x1,y=y1-5, angle=-45, add=add)
		
		i+=1
	return result

def getPinsBottom(pins, font, add="", forceColor=None):
	i=0
	result=""
	while i < len(pins["bottom"]):
		x1 = basex+widthPerPin//2 + i*(widthPerPin)
		y1 = basey+rectHeight
		x2 = x1
		y2 = y1+5
		if forceColor is not None:
			color=forceColor
		else:
			color = pins["bottom"][i][2]
		
		result+=textLine.format(x1,y1,x2,y2, color, add=add)
		result+=textNumber.format(x=x1-5, y=y1-5, text=pins["bottom"][i][0], font=font, color=color, add=add)
		result+=labelPinCommon(pins["bottom"][i], color=color).format(x=x1,y=y1+12, angle=45, add=add)
		i+=1
	return result


def getPinsRight(pins, font, add="", forceColor=None):
	i=0
	result=""
	while i < len(pins["right"]):
		x1 = basex+rectWidth
		y1 = basey+(heightPerPin//2)+ i*heightPerPin
		if len(pins["top"]) > 0:
			y1+=heightPerPin
		x2 = x1+5
		y2 = y1
		if forceColor is not None:
			color=forceColor
		else:
			color = pins["right"][i][2]
		result+=textLine.format(x1,y1,x2,y2, color, add=add)
		
		if pins["right"][i][0] < 10 :
			result+=textNumber.format(x=x1-charWidth-3, y=y1+5, text=pins["right"][i][0], font=font, color=color, add=add)
		else:
			result+=textNumber.format(x=x1-2*charWidth-3          , y=y1+5, text=pins["right"][i][0], font=font, color=color, add=add)
		result+=labelPinCommon(pins["right"][i], color=color).format(x=x1+6, y=y1+(charHeight//2), angle=0, add=add)
		i+=1
		
	return result


def getPinsLeft(pins, font, add="", forceColor=None):
	i=0
	result=""
	while i < len(pins["left"]):
		x1 = basex
		y1 = basey+(heightPerPin//2)+ i*heightPerPin
		if len(pins["top"]) > 0:
			y1+=heightPerPin
		x2 = x1-5
		y2 = y1
		if forceColor is not None:
			color=forceColor
		else:
			color = pins["left"][i][2]
		result+=textLine.format(x1,y1,x2,y2, color, add=add)
		result+=textNumber.format(x=x1+3, y=y1+5, text=pins["left"][i][0], font=font, color=color, add=add)
		result+=labelPinCommon(pins["left"][i], color=color).format(x=x1-6, y=y1+(charHeight//2), angle=0, add="text-anchor='end' "+add)
		i+=1
	return result


result+=getPinsTop(pins, fontFamily)
if args.lighten :
	result+=getPinsTop(pins, fontFamily, add="opacity='0.8' class='pinout-lighten-overlay'", forceColor="white")

result+=getPinsBottom(pins, fontFamily)
if args.lighten :
	result+=getPinsBottom(pins, fontFamily, add="opacity='0.8' class='pinout-lighten-overlay'", forceColor="white")

result+=getPinsRight(pins, fontFamily)
if args.lighten :
	result+=getPinsRight(pins, fontFamily, add="opacity='0.8' class='pinout-lighten-overlay'", forceColor="white")

result+=getPinsLeft(pins, fontFamily)
if args.lighten :
	result+=getPinsLeft(pins, fontFamily, add="opacity='0.8' class='pinout-lighten-overlay'", forceColor="white")



if args.background is not None:
	result = "<rect width='100%' height='100%' fill='{}' class='pinout-bg-rect'/>\n".format(args.background)+result
if args.svgTags:
	result = "<svg xmlns='http://www.w3.org/2000/svg' version='1.1'>\n"+result+"\n</svg>\n"

args.outfile.write(result)
