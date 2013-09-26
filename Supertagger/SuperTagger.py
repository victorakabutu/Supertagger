from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import musicbrainzngs
musicbrainzngs.set_useragent("SuperTagger App", "0.3", "http://example.com/music") #some simple class specific initialization

class SuperTagger(MP3):
	"""SuperTagger extends the Mutagen MP3 class by providing an interface to the musicbrainz system for 
	applications which need to tag MP3 files
	
	Class variables:
	__RESULTS_LIMIT__ is an integer representing the number of query results to fetch from musicbrainz
	"""
	
	#Mutable class variables
	__RESULTS_LIMIT__ = 5
	
	def __init__(self, fileName):
		MP3.__init__(self, fileName, ID3=EasyID3)
		self.results = []
		
	def get_search_results(self):
		"""Queries musicbrainz database using metadata from the file.
		
		Returns a list of results of size __RESULTS_LIMIT__"""
		
		file_name, old_album, old_title, old_artist, old_date, old_track_number = self.return_file_metadata()
		self.results = musicbrainzngs.search_recordings(artist = old_artist, recording = old_title, release = old_album, tnum = old_track_number, limit = SuperTagger.__RESULTS_LIMIT__)['recording-list']
		
		"""this sequence of if statements is designed to query the database using incomplete parameters.
		This is useful in the event that some of the pre-existing tag information is incorrect"""
		if not self.results:
			self.results = musicbrainzngs.search_recordings(recording = old_title, release = old_album, limit = SuperTagger.__RESULTS_LIMIT__)['recording-list']
		if not self.results:
			self.results = musicbrainzngs.search_recordings(artist = old_artist, recording = old_title, limit = SuperTagger.__RESULTS_LIMIT__)['recording-list']
		if not self.results: #TODO: Search by duration
			self.results = musicbrainzngs.search_recordings(recording = old_title, limit = SuperTagger.__RESULTS_LIMIT__)['recording-list']
		
		return self.results
		
	def return_result_metadata(self, i):
		"""Returns the ith result in easily parsable form. Return value is a tuple (artist, title, album, tracknumber, year	)
		
		Be sure to call get_search_results() first in order to have some results to return"""
		
		if not 0<= i < len(self.results): #Check for index errors
			raise IndexError('Results have indices between 0 and %s' % __RESULTS_LIMIT__)
			
		result = self.results[i] #Get the ith result
		
		#Extract values and return. Some care is required since search results may have malformed or missing entries
		artist = result['artist-credit-phrase'] if isinstance(result['artist-credit-phrase'], unicode) else result['artist-credit-phrase']
		title = result['title'].encode('utf-8') if isinstance(result['title'], unicode) else result['title']
		album = result['release-list'][0]['title'] if isinstance(result['release-list'][0]['title'], unicode) else result['release-list'][0]['title']
		tracknumber = result['release-list'][0]['medium-list'][1]['track-list'][0]['number']
		try:
			year = result['release-list'][0]['date'][:4]
		except KeyError:
			result['release-list'][0]['date'] = year = ''
		
		return artist, title, album, tracknumber, year	
		
	def return_file_metadata(self):
		"""Returns the file metadata in easily parsable form. Info is a dictionary with list values"""

		old_album, old_title, old_artist = self.get("album", [""])[0], self.get("title", [""])[0], self.get("artist", [""])[0]
		old_date, old_track_number = self.get("date", [""])[0], self.get('tracknumber', [""])[0].split('/')[0]

		return self.filename, old_album, old_title, old_artist, old_date, old_track_number

		
		
