#!/usr/bin/python3
"""
produces a SVG file with described pinout
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
	
	leadingSymbols = ["\\","/", ">", "<"]
	
	while word[0] in leadingSymbols:
		sym = word[0]
		word = word[1:]
		
		if sym == "\\":
			break
		
		elif sym == "/":
			features.append("not")
		elif sym == ">":
			features.append("arrow-out")
		elif sym == "<":
			features.append("arrow-in")
	
	# escape things that could confuse SVG parsers
	word = word.translate({
		ord("&") : "&amp;",
		ord("<") : "&lt;",
		ord(">") : "&gt;"
	})
	
	return (word, features)


def getNextSideCCW(side):
	"""
	returns the side that follows the given side, counter-clockwise
	"""
	if side == "left":
		return "bottom"
	if side == "bottom":
		return "right"
	if side == "right":
		return "top"
	if side == "top":
		return "left"

def getOppositeSide(side):
	"""
	returns the side that opposite
	"""
	if side == "left":
		return "right"
	if side == "bottom":
		return "top"
	if side == "right":
		return "left"
	if side == "top":
		return "bottom"

def getNextSide(side, params):
	"""
	returns the side that follows, according to params
	"""
	# TODO
	if params in ("quad", "qfp", "carrier", "square") :
		return getNextSideCCW(side)
	
	if params in ("dip", "parallel") :
		return getOppositeSide(side)
	
	return getNextSideCCW(side)

currentSection="top"
currentHighestNumberPlusOne=1
currentColor=strokeColor
for line in args.infile:
	line = line.strip()
	if line == "":
		continue
	if len(line)>1 and line[0] == "/" and line[1]== "/":
		continue
	if line[0] == "#":
		if len(line) == 1:
			continue
		inst = "".join(line[1:].split()).lower()
		if inst in ("top", "bottom", "left", "right", "title"):
			currentSection = inst
		elif inst == "mark" :
			marks.append(currentSection)
		elif inst == "nocolor" :
			currentColor = strokeColor
		elif inst == "nextside":
			currentSection = getNextSide(currentSection, "")
		else:
			currentColor = inst
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
			


# reorder pins according to mark position

if len(marks) == 0:
	if max(len(pins["top"]), len(pins["bottom"])) > max(len(pins["left"]), len(pins["right"])):
		refSide = "left"
	else:
		refSide = "top"
else:
	refSide = marks[-1]


if refSide == "top" :
	pins["right"].reverse()
	pins["top"].reverse()
elif refSide == "bottom" :
	pins["top"].reverse()
	pins["right"].reverse()
elif refSide == "left" :
	pins["right"].reverse()
	pins["top"].reverse()
elif refSide == "right" :
	pins["right"].reverse()
	pins["top"].reverse()


if args.verbose:
	import pprint
	print("== TITLE ==", file=sys.stderr)
	print(pprint.pformat(title["text"]), file=sys.stderr)
	print("== MARKS ==", file=sys.stderr)
	print(marks, file=sys.stderr)
	print("== PINS  ==", file=sys.stderr)
	print(pprint.pformat(pins), file=sys.stderr)
	
 
fontFamily = "monospace"

# best heuristics
# for the uneducated, this means guesses
# on MS EDge I measured 10 pt high letters
# with 15pt em
charHeight=15
charWidth = 8

widthPerPin = 25
heightPerPin = 22


basex = 30

longestLeftWordLen = 0
for i in pins["left"]:
	if len(i[1]) > longestLeftWordLen:
		longestLeftWordLen = len(i[1])
basex += longestLeftWordLen*charWidth

basey = 30

# a  bit more complicated, because diagonals
# trigonometry, tho
longestUpWordLen = 0
import re
for i in pins["top"]:
	wcp = re.sub("&.*?;", "_", i[1])
	# this is to avoid substitution characters like '&quot;' counting as
	# multiple characters
	# a bit heavy, though.
	if len(wcp) > longestUpWordLen:
		longestUpWordLen = len(wcp)

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

markSize = 7
if "top" in marks:
	startx = basex+(rectWidth//2)-markSize
	starty = basey
	endx = basex+(rectWidth//2)+markSize
	endy = basey
	result+="""\
<path d="M{sx} {sy}
		A {size} {size} 0 0 0 {ex} {ey}"
		stroke="{color}" fill="{color}" fill-opacity="0" stroke-width="2"/>

""".format(size=markSize, sx=startx, sy=starty, ex=endx, ey=endy,color=strokeColor)

if "bottom" in marks:
	startx = basex+(rectWidth//2)-markSize
	starty = basey+rectHeight
	endx = basex+(rectWidth//2)+markSize
	endy = basey+rectHeight
	result+="""\
<path d="M{sx} {sy}
		A {size} {size} 0 0 1 {ex} {ey}"
		stroke="{color}" fill="{color}" fill-opacity="0" stroke-width="2"/>

""".format(size=markSize, sx=startx, sy=starty, ex=endx, ey=endy, color=strokeColor)

if "right" in marks:
	startx = basex+rectWidth
	starty = basey+(rectHeight//2) - markSize
	endx = basex+rectWidth
	endy = basey+(rectHeight//2) + markSize
	result+="""\
<path d="M{sx} {sy}
		A {size} {size} 0 0 {ex} {ey}"
		stroke="{color}" fill="{color}" fill-opacity="0" stroke-width="2"/>

""".format(size=markSize, sx=startx, sy=starty, ex=endx, ey=endy, color=strokeColor)

if "left" in marks:
	startx = basex
	starty = basey+(rectHeight//2) - markSize
	endx = basex
	endy = basey+(rectHeight//2) + markSize
	result+="""\
<path d="M{sx} {sy}
		A {size} {size} 0 0 1 {ex} {ey}"
		stroke="{color}" fill="{color}" fill-opacity="0" stroke-width="2"/>

""".format(size=markSize, sx=startx, sy=starty, ex=endx, ey=endy, color=strokeColor)

## pins 

# yeah I know it's disgusting
# TODO refactor

textLine = "<line x1='{}' y1='{}' x2='{}' y2='{}' stroke='{}' stroke-width='2' {add}/>\n"
textNumber = "<text x='{x}' y='{y}' font-family='{font}' fill='{color}' {add}>{text}</text>\n"
textLabel = "<text x='{x}' y='{y}' transform='rotate({angle} {x} {y})' font-family='{font}' fill='{color}' {add}>{text}</text>\n\n"
textArrow = "<polygon points='{x1} {y1} {x2} {y2} {x3} {y3}' fill='{color}' {add}/>\n"
arrowD=5 #how big the arrows are

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
		p = pins["top"][i]
		x1 = basex+widthPerPin//2 + i*(widthPerPin)
		y1 = basey
		x2 = x1
		y2 = y1-5
		if forceColor is not None:
			color=forceColor
		else:
			color = p[2]
		
		result+=textNumber.format(x=x1-5, y=y1+12, text=p[0], font=font, color=color, add=add)
		
		if "arrow-in" in p[3]:
			result+=textArrow.format(x1=x1-arrowD,y1=y1-arrowD, x2=x1+arrowD, y2=y1-arrowD, x3=x1, y3=y1, color=color, add=add)
			y1-=arrowD
			y2-=arrowD
		
		result+=textLine.format(x1,y1,x2,y2, color, add=add)
		
		
		if "arrow-out" in p[3]:
			result+=textArrow.format(x1=x2-arrowD,y1=y2, x2=x2+arrowD, y2=y2, x3=x2, y3=y2-arrowD, color=color, add=add)
			y2-=arrowD
		
		result+=labelPinCommon(p, color=color).format(x=x1,y=y2-1, angle=-45, add=add)
		
		i+=1
	return result

def getPinsBottom(pins, font, add="", forceColor=None):
	i=0
	result=""
	while i < len(pins["bottom"]):
		p=pins["bottom"][i]
		x1 = basex+widthPerPin//2 + i*(widthPerPin)
		y1 = basey+rectHeight
		x2 = x1
		y2 = y1+5
		if forceColor is not None:
			color=forceColor
		else:
			color = p[2]
		
		result+=textNumber.format(x=x1-5, y=y1-5, text=p[0], font=font, color=color, add=add)
		
		if "arrow-in" in p[3]:
			result+=textArrow.format(x1=x1-arrowD,y1=y1+arrowD, x2=x1+arrowD, y2=y1+arrowD, x3=x1, y3=y1, color=color, add=add)
			y1+=arrowD
			y2+=arrowD
		
		result+=textLine.format(x1,y1,x2,y2, color, add=add)
		
		
		if "arrow-out" in p[3]:
			result+=textArrow.format(x1=x2-arrowD,y1=y2, x2=x2+arrowD, y2=y2, x3=x2, y3=y2+arrowD, color=color, add=add)
			y2+=arrowD
		
		
		result+=labelPinCommon(p, color=color).format(x=x1,y=y2+6, angle=45, add=add)
		i+=1
	return result


def getPinsRight(pins, font, add="", forceColor=None):
	i=0
	result=""
	while i < len(pins["right"]):
		p=pins["right"][i]
		x1 = basex+rectWidth
		y1 = basey+(heightPerPin//2)+ i*heightPerPin
		if len(pins["top"]) > 0:
			y1+=heightPerPin
		x2 = x1+5
		y2 = y1
		if forceColor is not None:
			color=forceColor
		else:
			color = p[2]
		
		
		if pins["right"][i][0] < 10 :
			result+=textNumber.format(x=x1-charWidth-3, y=y1+5, text=p[0], font=font, color=color, add=add)
		else:
			result+=textNumber.format(x=x1-2*charWidth-3, y=y1+5, text=p[0], font=font, color=color, add=add)
		
		if "arrow-in" in p[3]:
			result+=textArrow.format(x1=x1+arrowD,y1=y1-arrowD, x2=x1+arrowD, y2=y1+arrowD, x3=x1, y3=y1, color=color, add=add)
			x1+=arrowD
			x2+=arrowD
		
		result+=textLine.format(x1,y1,x2,y2, color, add=add)
		
		if "arrow-out" in p[3]:
			result+=textArrow.format(x1=x2,y1=y2-arrowD, x2=x2, y2=y2+arrowD, x3=x2+arrowD, y3=y2, color=color, add=add)
			x2+=arrowD
		
		result+=labelPinCommon(p, color=color).format(x=x2+1, y=y2+(charHeight//2), angle=0, add=add)
		i+=1
		
	return result


def getPinsLeft(pins, font, add="", forceColor=None):
	i=0
	result=""
	while i < len(pins["left"]):
		p=pins["left"][i]
		x1 = basex
		y1 = basey+(heightPerPin//2)+ i*heightPerPin
		if len(pins["top"]) > 0:
			y1+=heightPerPin
		x2 = x1-5
		y2 = y1
		if forceColor is not None:
			color=forceColor
		else:
			color = p[2]
		
		result+=textNumber.format(x=x1+3, y=y1+5, text=p[0], font=font, color=color, add=add)
		if "arrow-in" in p[3]:
			result+=textArrow.format(x1=x1-arrowD,y1=y1-arrowD, x2=x1-arrowD, y2=y1+arrowD, x3=x1, y3=y1, color=color, add=add)
			x1-=arrowD
			x2-=arrowD
		
		result+=textLine.format(x1,y1,x2,y2, color, add=add)
		
		if "arrow-out" in p[3]:
			result+=textArrow.format(x1=x2,y1=y2-arrowD, x2=x2, y2=y2+arrowD, x3=x2-arrowD, y3=y2, color=color, add=add)
			x2-=arrowD
		
		result+=labelPinCommon(p, color=color).format(x=x2-1, y=y1+(charHeight//2), angle=0, add="text-anchor='end' "+add)
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
