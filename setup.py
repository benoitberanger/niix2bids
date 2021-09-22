import setuptools
import metadata

with open('README.md') as f:
    long_description = f.readlines()

setuptools.setup(
    name="niix2bids",
    version=metadata.get_version(),
    author='Benoît Béranger',
    author_email='benoit.beranger@icm-institute.org',
    url='https://github.com/benoitberanger/niix2bids.git',
    description='Automatic BIDS architecture',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='GPL3',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'niix2bids = niix2bids.cli:main'
        ]
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GLP3",
        "Operating System :: OS Independent",
    ),
    keywords='MRI BIDS',
    zip_safe=False
)
