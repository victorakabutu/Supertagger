"""Application for tagging mp3 files in directories.
Simply run 'python mp3_tagger.py' at shell (no arguments required).

Windows users may need to enter directory paths using forward slashes.
You may use either relative or absolute paths.
"""

__author__ = "Victor Akabutu (iversion@gmail.com)"
__version__ = "$Revision: 0.3 $"
__date__ = "$Date: 2013/09/23 13:08:58 $"
__copyright__ = "Copyright (c) 2013 Victor Akabutu"

import os
import sys
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
 
#For future use to update ID3v1 tags (Windows compatibility).
"""
def stripnulls(data):
    "strip whitespace and nulls"
    return data.replace("\00", " ").strip()

#This idea of using a UserDict-like object is due to Mark Pilgrim of 'Dive Into Python'
class FileInfo(dict):
    A base class for storing file metadata. Objects are dicts
    def __init__(self, filename=None):
        self["name"] = filename
    
class MP3FileInfo(FileInfo):
    "store ID3v1.0 MP3 tags"
    tagDataMap = {"title"   : (  3,  33, stripnulls),
                  "artist"  : ( 33,  63, stripnulls),
                  "album"   : ( 63,  93, stripnulls),
                  "year"    : ( 93,  97, stripnulls),
                  "comment" : ( 97, 126, stripnulls),
                  "genre"   : (127, 128, ord)}
    
    def __parse(self, filename):
        "parse ID3v1.0 tags from MP3 file"
        self.clear()
        try:
            fsock = open(filename, "rb", 0)
            try:
                fsock.seek(-128, 2)
                tagdata = fsock.read(128)
            finally:
                fsock.close()
            if tagdata[:3] == 'TAG':
                for tag, (start, end, parseFunc) in self.tagDataMap.items():
                    self[tag] = parseFunc(tagdata[start:end])
        except IOError:
            pass

    def __setitem__(self, key, item):
        if key == "name" and item:
            self.__parse(item)
        FileInfo.__setitem__(self, key, item)"""


def list_directory_shallow(directory, fileExtList):
    """list_directory_shallow parses directory for files with extension in list fileExtList
    Example usage: list_directory_shallow('C:\Documents\Music', ['.mp3', '.wav'])

    Note that list_directory_shallow() does not recursively examine subfoldres of directory (see list_directory_deep())."""

    #stores filenames from directory as strings (like 'nirvana.mp3') in fileList. normcase() converts to lower case for OS/Win
    fileList = [os.path.normcase(f) for f in os.listdir(directory)]
    #convert all filenames in fileList to absolute file paths
    fileList = [os.path.join(directory, f) for f in fileList if os.path.splitext(f)[1] in fileExtList]

    return collect_tags(fileList)

def list_directory_deep(directory, fileExtList):
	"""list_directory_deep parses directory and its subfolders for files with extension in list fileExtList
	Example usage: list_directory_shallow('C:\Documents\Music', ['.mp3', '.wav'])"""

	#TODO: Replace one layer search with recursive deep search
	import glob

	"""glob uses escaped back slashes so we change all forward slashes to escaped back slashes and
	append an escaped back slash at the end of directory (if necessary) to keep things consistent"""
	directory.replace("/", "\\")
	if directory[-1]!="\\":
		directory += "\\"

	fileList = []

	for ext in fileExtList:
		fileList.extend(glob.glob('%s*\\*%s' % (directory, ext)))

	return collect_tags(fileList)

def collect_tags(fileList):
    """Takes argument fileList, a list of file path strings, and returns a list of Mutagen MP3 objects
    corresponding to each file path"""
    if not fileList:
        print 'No files found in %s. Exiting..' % (directory)
        sys.exit(0)
        
    return [MP3(f, ID3=EasyID3) for f in fileList]

def take_input():
	"""Asks user to specify music directory to search, whether search should be 1 layer deep, and whether
	to rename tagged files"""

	f = raw_input('Please enter music directory: ')

	if not os.path.isdir(f):
		print 'Path is not a directory. Exiting...'
		sys.exit(1)

	print "\nYou may either search only files in this folder or search each subdirectory in \
	this folder (useful for music directories with many subfolders). These are mutually exclusive options.\n"
	deep_search = raw_input("Search all subdirectories within this folder? (y/n): ")

	if deep_search and deep_search[0].lower() == 'y':
		list_directory = list_directory_deep
	else:
		list_directory = list_directory_shallow

	r = raw_input("Rename files after tagging (Format: 'Track number - Track Title.mp3')?  y/n: ")

	rename_tagged_files = True if r and r[0].lower() == 'y' else False

	return f, list_directory, rename_tagged_files

if __name__ == "__main__":

	import musicbrainzngs
	musicbrainzngs.set_useragent("Music Tagger App", "0.1", "http://example.com/music")

	count, choices = 0, []

	directory, list_directory, rename_tagged_files = take_input()
	print '\n'

	def print_result_header():
		print "   #   " + "**Title**".ljust(17) + "   **Album**".ljust(21) + "**Artist**".ljust(17) + "**Year**"

	def extract_metadata_from_result(result):
		artist = result['artist-credit-phrase'] if isinstance(result['artist-credit-phrase'], unicode) else result['artist-credit-phrase']
		title = result['title'].encode('utf-8') if isinstance(result['title'], unicode) else result['title']
		album = result['release-list'][0]['title'] if isinstance(result['release-list'][0]['title'], unicode) else result['release-list'][0]['title']
		tracknumber = result['release-list'][0]['medium-list'][1]['track-list'][0]['number']
		try:
			year = result['release-list'][0]['date'][:4]
		except KeyError:
			result['release-list'][0]['date'] = year = ''
		
		return artist, title, album, tracknumber, year
		
	def ask_to_specify_correct_tags(choices, rename_tagged_files):
		"""Prompt user to specify which files to tag. Files are tagged and renamed if rename_tagged_files = True."""

		print 'For each of the above results, please enter the corresponding track to extract from.',
		print 'Eg. To apply the second result for the first track, to apply no results from the second track,',		
		print ' and to apply the 5th result for the 3rd track, you would enter "2 * 5"'
		print '\nChoices are delimited by spaces and results can be rejected by using "*". Unparsable inputs are ignored.\n'
		seq = raw_input("Please enter your sequence: ")

		def clean_filename(filename):
			"""clean_filename(filename) removes filesystem non-compliant characters from the string argument filename"""
			import string
			valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
			return ''.join(c for c in filename if c in valid_chars)
			
		for i, item in enumerate(seq.split()[:5]):
			if item.isdigit() and 1 <= int(item) <= 5: #TODO: Modify hard coding
				f, result = choices[i][0], choices[i][1][int(item)-1]

				artist, title, album, tracknumber, year = extract_metadata_from_result(result)

				f["artist"] = artist
				f["title"] = title
				f["album"] = album
				f["tracknumber"] = tracknumber
				f.save()

				if rename_tagged_files: 
					os.rename(f.filename, os.path.join(os.path.split(f.filename)[0], "%s - %s.mp3" % (tracknumber, clean_filename(title))))
		#TODO
		count = 0
		choices = list()

	def print_file_info_and_return_metadata(info):
		"""Prints the given file's information neatly. Info is a dictionary with list values"""

		#TODO: Remove hard coding of column widths
		old_album, old_title, old_artist = info.get("album", [""])[0], info.get("title", [""])[0], info.get("artist", [""])[0]
		old_date, old_track_number = info.get("date", [""])[0], info.get('tracknumber', [""])[0].split('/')[0]
		
		print os.path.split(info.filename)[1] + '\n'
		print "Album".ljust(20) + "Title".ljust(20) + "Artist".ljust(15) + "#".ljust(4) + "Year"
		print old_album[:18].ljust(20) + old_title[:16].ljust(20) + old_artist[:11].ljust(15) + old_track_number.ljust(4) + old_date
		print

		return old_album, old_title, old_artist, old_date, old_track_number
    
	def get_search_results(old_album, old_title, old_artist, old_date, old_track_number):
		results = musicbrainzngs.search_recordings(artist = old_artist, recording = old_title, release = old_album, tnum = old_track_number, limit = 5)

		"""this sequence of if statements is designed to query the database using incomplete parameters.
		This is useful in the event that some of the pre-existing tag information is incorrect"""
		if not results['recording-list']:
			results = musicbrainzngs.search_recordings(recording = old_title, release = old_album, limit = 5)
		if not results['recording-list']:
			results = musicbrainzngs.search_recordings(artist = old_artist, recording = old_title, limit = 5)
		if not results['recording-list']: #TODO: Search by duration
			results = musicbrainzngs.search_recordings(recording = old_title, limit = 5)
		
		return results['recording-list']
		
	for info in list_directory(directory, [".mp3"]):
		if count==5:
			ask_to_specify_correct_tags(choices, rename_tagged_files)
			print
		count += 1

		old_album, old_title, old_artist, old_date, old_track_number = print_file_info_and_return_metadata(info)

		if not old_title: #if file does not specify a title
			print_result_header()
			print "No results found - missing title.\n"
			continue

		results = get_search_results(old_album, old_title, old_artist, old_date, old_track_number)

		print_result_header()
		
		if not results:
			print "No results found"
			continue
			
		choices.append((info, results)) #we pair each file with its results list to facilitate later tagging

		for i, result in enumerate(results, 1):
			artist, title, album, tracknumber, year = extract_metadata_from_result(result)
			
			print str(i) + ")", #number results on screen
			print tracknumber.ljust(4) + title[:18].ljust(20) + album[:16].ljust(18) + artist[:15].ljust(17) + year

		print '-'*75
		print

	if choices:
		ask_to_specify_correct_tags(choices, rename_tagged_files)
		print
