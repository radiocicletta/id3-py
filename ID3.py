# ID3.py version 1.2

# Module for manipulating ID3 informational tags in MP3 audio files
# $Id$

# Written 2 May 1999 by Ben Gertzfield <che@debian.org>
# This work is released under the GNU GPL, version 2 or later.

# Modified 10 June 1999 by Arne Zellentin <arne@unix-ag.org> to
# fix bug with overwriting last 128 bytes of a file without an
# ID3 tag

# Patches from Jim Speth <speth@end.com> and someone whose email
# I've forgotten at the moment (huge apologies, I didn't save the
# entire mail, just the patch!) for so-called ID3 v1.1 support,
# which makes the last two bytes of the comment field signify a
# track number. If the first byte is null but the second byte
# is not, the second byte is assumed to signify a track number.

# Also thanks to Jim for the simple function to remove nulls and
# whitespace from the ends of ID3 tags. I'd like to add a boolean
# flag defaulting to false to the ID3() constructor signifying whether
# or not to remove whitespace, just in case old code depended on the
# old behavior for some reason, but that'd make any code that wanted
# to use the stripping behavior not work with old ID3.py. Bleh.

# This is the first thing I've ever written in Python, so bear with
# me if it looks terrible. In a few years I'll probably look back at
# this and laugh and laugh..

# Constructor:
#
#   ID3(file, filename='unknown filename', as_tuple=0)
#     Opens file and tries to parse its ID3 header. If the ID3 header
#     is invalid or the file access failed, raises InvalidTagError.
#
#     file can either be a string specifying a filename which will be
#     opened in binary mode, or a file object.  If it's a file object,
#     the filename should be passed in as the second argument to this
#     constructor, otherwise file.name will be used in error messages
#     (or 'unknown filename' if that's missing). Also, if it's a file
#     object, it *must* be opened in r+ mode (or equivalent) to allow
#     both reading and writing.
#
#     If as_tuple is true, the dictionary interface to ID3 will return
#     tuples containing one string each instead of a string, for
#     compatibility with the ogg.vorbis module.
#
#     When object is deconstructed, if any of the class data (below) have
#     been changed, opens the file again read-write and writes out the
#     new header. If the header is to be deleted, truncates the last
#     128 bytes of the file.
#
#     Note that if ID3 cannot write the tag out to the file upon
#     deconstruction, InvalidTagError will be raised and ignored
#     (as we are in __del__, and exceptions just give warnings when
#     raised in __del__.)

# Class Data of Interest:
#
#   Note that all ID3 fields, unless otherwise specified, are a maximum of
#   30 characters in length. If a field is set to a string longer than
#   the maximum, it will be truncated when it's written to disk.
#
#   As of ID3 version 1.2, there are two interfaces to this data.
#   You can use the direct interface or the dictionary-based interface.
#   The normal dictionary methods (has_key, get, keys, values, items, etc.)
#   should work on an ID3 object.  You can assign values to either the
#   dictionary interface or the direct interface, and they will both
#   reflect the changes.
#
#   If any of the fields are not defined in the ID3 tag, the dictionary
#   based interface will not contain a key for that field!  Test with
#   ID3.has_key('ARTIST') etc. first.
#
#   ID3.title or ID3['TITLE']
#     Title of the song.
#   ID3.artist or ID3['ARTIST']
#     Artist/creator of the song.
#   ID3.album or ID3['ALBUM']
#     Title of the album the song is from.
#   ID3.year or ID3['YEAR']
#     Year the song was released. Maximum of 4 characters (Y10K bug!)
#   ID3.genre
#     Genre of the song. Integer value from 0 to 255. Genre specification
#     comes from (sorry) WinAMP. http://mp3.musichall.cz/id3master/faq.htm
#     has a list of current genres; I spell-checked this list against
#     WinAMP's by running strings(1) on the file Winamp/Plugins/in_mp3.dll
#     and made a few corrections.
#   ID3['GENRE']
#     String value corresponding to the integer in ID3.genre.  If there
#     is no genre string available for the ID3.genre number, this will
#     be set to "Unknown Genre".
#   ID3.comment or ID3['COMMENT']
#     Comment about the song.
#   ID3.track or ID3['TRACKNUMBER']
#     Track number of the song. None if undefined.
#     NOTE: ID3['TRACKNUMBER'] will return a *string* containing the
#     track number, for compatibility with ogg.vorbis.
#
#   ID3.genres
#     List of all genres. ID3.genre above is used to index into this
#     list. ID3.genres is current as of WinAMP 1.92.

# Methods of Interest:
#
#   write()
#     If the class data above have changed, opens the file given
#     to the constructor read-write and writes out the new header.
#     If the header is flagged for deletion (see delete() below)
#     truncates the last 128 bytes of the file to remove the header.
#
#     NOTE: write() is called from ID3's deconstructor, so it's technically
#     unnecessary to call it. However, write() can raise an InvalidTagError,
#     which can't be caught during deconstruction, so generally it's
#     nicer to call it when writing is desired.
#
#   delete()
#     Flags the ID3 tag for deletion upon destruction of the object
#
#   find_genre(genre_string)
#     Searches for the numerical value of the given genre string in the
#     ID3.genres table. The search is performed case-insensitively. Returns
#     an integer from 0 to len(ID3.genres).
#
#   legal_genre(genre_number)
#     Checks if genre_number is a legal index into ID3.genres.  Returns
#     true if so, false otherwise.
#
#   as_dict()
#     Returns just the dictionary containing the ID3 tag fields.
#     See the notes above for the dictionary interface.
#

import string
import locale
from typing import Any, Union, cast, Dict
from io import BufferedReader

try:
    string_types = [bytes, str]
except AttributeError:                  # if no unicode support

    string_types = [bytes]


def lengthen(string: bytes, num_spaces: int) -> bytes:
    string = string[:num_spaces]
    return string + (b' ' * (num_spaces - len(string)))


# We would normally use string.rstrip(), but that doesn't remove \0 characters.
def strip_padding(s: bytes) -> bytes:
    while len(s) > 0 and s[-1] in (string.whitespace + "\0").encode():
        s = s[:-1]

    return s


class InvalidTagError(BaseException):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg


class ID3:

    genres = [
        "Blues", "Classic Rock", "Country", "Dance", "Disco", "Funk",
        "Grunge", "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies", "Other",
        "Pop", "R&B", "Rap", "Reggae", "Rock", "Techno", "Industrial",
        "Alternative", "Ska", "Death Metal", "Pranks", "Soundtrack",
        "Euro-Techno", "Ambient", "Trip-Hop", "Vocal", "Jazz+Funk", "Fusion",
        "Trance", "Classical", "Instrumental", "Acid", "House", "Game",
        "Sound Clip", "Gospel", "Noise", "Alt. Rock", "Bass", "Soul",
        "Punk", "Space", "Meditative", "Instrum. Pop", "Instrum. Rock",
        "Ethnic", "Gothic", "Darkwave", "Techno-Indust.", "Electronic",
        "Pop-Folk", "Eurodance", "Dream", "Southern Rock", "Comedy",
        "Cult", "Gangsta", "Top 40", "Christian Rap", "Pop/Funk", "Jungle",
        "Native American", "Cabaret", "New Wave", "Psychadelic", "Rave",
        "Showtunes", "Trailer", "Lo-Fi", "Tribal", "Acid Punk", "Acid Jazz",
        "Polka", "Retro", "Musical", "Rock & Roll", "Hard Rock", "Folk",
        "Folk/Rock", "National Folk", "Swing", "Fusion", "Bebob", "Latin",
        "Revival", "Celtic", "Bluegrass", "Avantgarde", "Gothic Rock",
        "Progress. Rock", "Psychadel. Rock", "Symphonic Rock", "Slow Rock",
        "Big Band", "Chorus", "Easy Listening", "Acoustic", "Humour",
        "Speech", "Chanson", "Opera", "Chamber Music", "Sonata", "Symphony",
        "Booty Bass", "Primus", "Porn Groove", "Satire", "Slow Jam",
        "Club", "Tango", "Samba", "Folklore", "Ballad", "Power Ballad",
        "Rhythmic Soul", "Freestyle", "Duet", "Punk Rock", "Drum Solo",
        "A Capella", "Euro-House", "Dance Hall", "Goa", "Drum & Bass",
        "Club-House", "Hardcore", "Terror", "Indie", "BritPop", "Negerpunk",
        "Polsk Punk", "Beat", "Christian Gangsta Rap", "Heavy Metal",
        "Black Metal", "Crossover", "Contemporary Christian", "Christian Rock",
        "Merengue", "Salsa", "Thrash Metal", "Anime", "Jpop", "Synthpop"
        ]

    def __init__(self, file: Union[str, bytes, BufferedReader], name: str='unknown filename', as_tuple:int=0):
        if type(file) in string_types:
            self.filename = file
        # We don't open in r+b if we don't have to, to allow read-only access
            self.file = open(cast(str, file), 'rb')
            self.can_reopen = 1
        elif hasattr(file, 'seek'):  # assume it's an open file
            if name == 'unknown filename' and hasattr(file, 'name'):
                self.filename = file.name
            else:
                self.filename = name

            self.file = cast(BufferedReader, file)
            self.can_reopen = 0

        self.d: Dict[str, Any] = {}
        self.as_tuple = as_tuple
        self.delete_tag = 0
        self.zero()
        self.modified = 0
        self.has_tag = 0
        self.had_tag = 0

        try:
            self.file.seek(-128, 2)

        except IOError as msg:
            self.modified = 0
            raise InvalidTagError("Can't open %s: %s" % (str(self.filename), msg))
            return

        try:
            if self.file.read(3) == b'TAG':
                self.has_tag = 1
                self.had_tag = 1
                self.title = self.file.read(30)
                self.artist = self.file.read(30)
                self.album = self.file.read(30)
                self.year = self.file.read(4)
                self.comment = self.file.read(30)

                if self.comment[-2] == 0 and self.comment[-1] != 0:
                    self.track = self.comment[-1]
                    self.comment = self.comment[:-2]
                else:
                    self.track = None # type: ignore

                self.genre = self.file.read(1)

                self.title = strip_padding(self.title)
                self.artist = strip_padding(self.artist)
                self.album = strip_padding(self.album)
                self.year = strip_padding(self.year)
                self.comment = strip_padding(self.comment)

                self.setup_dict()

        except IOError as msg:
            self.modified = 0
            raise InvalidTagError(
                "Invalid ID3 tag in %s: %s" % (
                    str(self.filename),
                    msg)
            )
        self.modified = 0

    def setup_dict(self):
        self.d = {}
        if self.title:
            self.d["TITLE"] = self.tupleize(self.title)
        if self.artist:
            self.d["ARTIST"] = self.tupleize(self.artist)
        if self.album:
            self.d["ALBUM"] = self.tupleize(self.album)
        if self.year:
            self.d["YEAR"] = self.tupleize(self.year)
        if self.comment:
            self.d["COMMENT"] = self.tupleize(self.comment)
        if self.legal_genre(self.genre):
            self.d["GENRE"] = self.tupleize(self.genres[self.genre])
        else:
            self.d["GENRE"] = self.tupleize(b"Unknown Genre")
        if self.track:
            self.d["TRACKNUMBER"] = self.tupleize(bytes(self.track))

    def delete(self):
        self.zero()
        self.delete_tag = 1
        self.has_tag = 0

    def zero(self):
        self.title = b''
        self.artist = b''
        self.album = b''
        self.year = b''
        self.comment = b''
        self.track = b''
        self.genre = 255  # 'unknown', not 'blues'
        self.setup_dict()

    def tupleize(self, s: Any) -> tuple:
        if self.as_tuple and not isinstance(s, tuple):
            return (s,)
        return s

    def find_genre(self, genre_to_find:Union[str, bytes]):
        i = 0
        find_me = str(genre_to_find).lower()

        for genre in self.genres:
            if str(genre).lower() == find_me:
                break
            i = i + 1
        if i == len(self.genres):
            return -1
        return i

    def legal_genre(self, genre: Any):
        if isinstance(genre, int) and 0 <= genre < len(self.genres):
            return 1
        return 0

    def write(self):
        if self.modified:
            try:
                # We see if we can re-open in r+ mode now, as we need to write
                if self.can_reopen:
                    self.file = open(self.filename, 'r+b')

                if self.had_tag:
                    self.file.seek(-128, 2)
                else:
                    self.file.seek(0, 2)  # a new tag is appended at the end
                if self.delete_tag and self.had_tag:
                    self.file.truncate()
                    self.had_tag = 0
                elif self.has_tag:
                    go_on = 1
                    if self.had_tag:
                        if self.file.read(3) == b"TAG":
                            self.file.seek(-128, 2)
                        else:
                            # someone has changed the file in the mean time
                            go_on = 0
                            raise IOError("File has been modified, losing tag changes")
                    if go_on:
                        self.file.write(b'TAG')
                        self.file.write(lengthen(self.title, 30))
                        self.file.write(lengthen(self.artist, 30))
                        self.file.write(lengthen(self.album, 30))
                        self.file.write(lengthen(self.year, 4))

                        comment = lengthen(self.comment, 30)

                        if 0 < int.from_bytes(self.track, "big") < 255:
                            comment = comment[:-2] + "\0" + self.track

                        self.file.write(comment)

                        if 0 < int.from_bytes(self.genre, "big") < 255:
                            self.genre = 255
                        self.file.write(self.genre)
                        self.had_tag = 1
                self.file.flush()
            except IOError as msg:
                raise InvalidTagError(
                    "Cannot write modified ID3 tag to %s: %s" % (
                        self.filename, msg)
                )
            else:
                self.modified = 0

    def as_dict(self):
        return self.d

    def items(self):
        return map(None, list(self.keys()), list(self.values()))

    def keys(self):
        return list(self.d.keys())

    def values(self):
        if self.as_tuple:
            return [x[0].decode() for x in list(self.d.values())]
        return [x.decode() for x in list(self.d.values())]

    def has_key(self, k):
        return k in self.d

    def get(self, k: str, x: Any=None):
        if k in self.d:
            return self.d[k].decode()
        else:
            return x

    def __getattr__(self, k:str, x:Any=None):
        if k in self.d:
            return self.d[k].decode()
        else:
            try:
                return self.__getattribute__(k)
            except AttributeError:
                return x

    def __getitem__(self, k:str):
        return self.d[k].decode()

    def __setitem__(self, k:str, v:Any):

        if k not in ['TITLE', 'ARTIST', 'ALBUM', 'YEAR', 'COMMENT', 'TRACKNUMBER', 'GENRE']:
            return
        if k == 'TRACKNUMBER':
            if isinstance(v, int):
                self.track = v
            else:
                self.track = locale.atoi(v)
            self.d[k] = self.tupleize(v)
        elif k == 'GENRE':
            if isinstance(v, int):
                if self.legal_genre(v):
                    self.genre = v # type: ignore
                    self.d[k] = self.tupleize(self.genres[cast(int, v)])
                else:
                    self.genre = v # type: ignore
                    self.d[k] = self.tupleize(b"Unknown Genre")
            else:
                self.genre = self.find_genre(v)
                if self.genre == -1:
                    print(v, "not found")
                    self.genre = 255 # type: ignore
                    self.d[k] = self.tupleize(b"Unknown Genre")
                else:
                    print(self.genre, v)
                    self.d[k] = self.tupleize(v)
        else:
            self.__dict__[str(k).lower()] = v.encode()
            self.d[k] = self.tupleize(v.encode())
        self.__dict__['modified'] = 1
        self.__dict__['has_tag'] = 1

    def __del__(self):
        self.write()

    def __str__(self):
        print("!!!!!!")
        if self.has_tag:
            if self.genre is not None and int.from_bytes(self.genre, "big") >= 0 and \
                   int.from_bytes(self.genre, "big") < len(self.genres):
                genre = self.genres[int.from_bytes(self.genre, "big")]
            else:
                genre = b'Unknown'

            if self.track is not None:
                track = str(self.track)
            else:
                track = b'Unknown'

            return "File   : %s\nTitle  : %-30.30s  Artist: %-30.30s\nAlbum  : %-30.30s  Track : %s  Year: %-4.4s\nComment: %-30.30s  Genre : %s (%i)" % (self.filename, self.title, self.artist, self.album, track, self.year, self.comment, genre, int.from_bytes(self.genre, "big"))
        return "%s: No ID3 tag." % self.filename

    # intercept setting of attributes to set self.modified
    def __setattr__(self, name:str, value:Any):
        if name in ['title', 'artist', 'album', 'year', 'comment',
                    'track', 'genre']:
            self.__dict__['modified'] = 1
            self.__dict__['has_tag'] = 1
            if name == 'track' and value is not None:
                self.__dict__['d']['TRACKNUMBER'] = self.tupleize(bytes(value))
            elif name == 'genre':
                if self.legal_genre(value):
                    self.__dict__['d']['GENRE'] = self.tupleize(self.genres[value])
                else:
                    self.__dict__['d']['GENRE'] = self.tupleize(b'Unknown Genre')
            else:
                self.__dict__['d'][str(name).upper()] = self.tupleize(value)
            self.__dict__[name] = bytes(value)
        else:
            self.__dict__[name] = value
