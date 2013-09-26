from setuptools import setup

setup(name = 'MP3 Supertagger',
	version = '0.3',
	description = 'MP3 Supertagger properly tags all MP3s in a specified folder',
	author = 'Victor Akabutu',
	author_email = 'iversion@gmail.com',
	install_requires = ['mutagen>=1.22', 'musicbrainzngs >=0.4']
	packages = find_packages()
)
