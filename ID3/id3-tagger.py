#!/usr/bin/env python

import getopt, string, re, sys
from ID3 import *

version = 0.1
name = 'id3-tagger.py'

def usage():
    sys.stderr.write(
"This is %s version %0.1f, a tool for setting ID3 tags in MP3 files.\n\n\
Usage: %s [-t title] [-a artist] [-A album] [-y year] [-c comment] \n\
       %s [-g genre] [-d] [-h] [-v] file1 [file2 ...]\n\n\
-d: Delete the ID3 tag from specified file(s) completely\n\
-h: Display this text\n\
-v: Display the version of this program\n\n\
With no arguments, display the ID3 tag of the given file(s).\n" % 
       (name, version, name, ' ' * len(name)))

def main():
    options = {}

    try:
	opts, args = getopt.getopt(sys.argv[1:], 't:a:A:y:c:g:dhvl')
    except getopt.error, msg:
	print msg
	usage()
	sys.exit(2)

    for opt, arg in opts:
	if opt == '-v':
	    sys.stderr.write("This is %s version %0.1f.\n" % (name, version))
	    sys.exit(0)
	if opt == '-h':
	    usage()
	    sys.exit(0)
	if opt == '-t':
	    options['title'] = arg
	if opt == '-a':
	    options['artist'] = arg
	if opt == '-A':
	    options['album'] = arg
	if opt == '-y':
	    options['year'] = arg
	if opt == '-c':
	    options['comment'] = arg
	if opt == '-g':
	    options['genre'] = arg
	if opt == '-d':
	    options['delete'] = 1

    if len(args) == 0:
	usage()
	sys.exit(2)

    for file in args:
	try:
	    id3info = ID3(file)

	    if options.has_key('title'):
		id3info.title = options['title']
	    if options.has_key('artist'):
		id3info.artist = options['artist']
	    if options.has_key('album'):
		id3info.album = options['album']
	    if options.has_key('year'):
		id3info.year = options['year']
	    if options.has_key('comment'):
		id3info.comment = options['comment']
	    if options.has_key('genre'):
		if re.match('^\d+$', options['genre']):
		    id3info.genre = int(options['genre'])
		else:
		    id3info.genre = id3info.find_genre(options['genre'])
	    if options.has_key('delete'):
		id3info.delete()

	    print id3info

	except InvalidTagError, msg:
	    print "Invalid ID3 tag:", msg
	    continue

main()
