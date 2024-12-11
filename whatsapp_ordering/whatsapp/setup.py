import setuptools
from sys import version

if version < '2.2.3':
	from distutils.dist import DistributionMetadata
	DistributionMetadata.classifiers = None
	DistributionMetadata.download_url = None
	
from distutils.core import setup


setuptools.setup(
                    name='whatsapp',
                    version='1.0.10',
                    author='@rockscripts',
                    author_email='codesystems.co@gmail.com',
                    description='Whatsapp Business for ordering comunication',
                    install_requires=[],
                    platforms='any',
                    url='',
                    packages=['whatsapp'],
                    python_requires='>=2.7.*',
                )
