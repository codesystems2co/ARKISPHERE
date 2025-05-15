from setuptools import setup, find_packages

setup(
    name='bitbucket',
    version='1.0.110',
    author='@arkiphere',
    author_email='codesystems.co@gmail.com',
    description='Bitbucket Integration with OAuth Support',
    long_description='''
    A Python library for Bitbucket Cloud integration with OAuth support.
    Built on top of atlassian-python-api for enhanced functionality.
    ''',
    long_description_content_type='text/markdown',
    url='https://arkiphere.cloud',
    packages=find_packages(),
    install_requires=[
        'atlassian-python-api>=3.41.1',
        'requests>=2.31.0',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
