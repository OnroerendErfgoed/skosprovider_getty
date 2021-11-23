import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

packages = [
    'skosprovider_getty'
]

requires = [
    'skosprovider>=0.7.0',
    'requests',
    'rdflib'
]

setup(
    name='skosprovider_getty',
    version='0.5.1',
    description='Skosprovider implementation of the Getty Vocabularies',
    long_description=README + '\n\n' + CHANGES,
    long_description_content_type='text/x-rst',
    packages=packages,
    include_package_data=True,
    install_requires=requires,
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    author='Flanders Heritage Agency',
    author_email='ict@onroerenderfgoed.be',
    url='https://github.com/OnroerendErfgoed/skosprovider_getty',
    keywords='getty skos skosprovider vocabulary AAT TGN ULAN'
)
