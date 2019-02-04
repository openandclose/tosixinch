
"""tosixinch setup file."""

# from setuptools import setup, find_packages
from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

with open('VERSION') as f:
    version = f.read().strip()


setup(
    name='tosixinch',
    version=version,
    url='https://github.com/openandclose/tosixinch',
    license='MIT',
    author='Open Close',
    author_email='openandclose23@gmail.com',
    description='Browser to e-reader in a few minutes',
    long_description=readme,
    # https://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Utilities',
    ],
    keywords='html pdf lxml extraction conversion e-reader kindle kobo',
    # packages=find_packages(exclude=['tests']),
    packages=['tosixinch', 'tosixinch.process'],
    package_data={
        'tosixinch': ['data/*.ini', 'data/css/*.css', 'script/*', ],
    },
    entry_points={
        'console_scripts': [
            'tosixinch = tosixinch.main:main',
        ],
    },
    python_requires='~=3.5',
    extras_require={
        'test': ['lxml', 'pytest'],
        'dev': ['lxml', 'pytest', 'sphinx'],
    },
    zip_safe=False,
)
