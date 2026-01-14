from setuptools import setup

setup(
    name='jsonquery',
    version='1.0.0',
    description='Smart JSON/YAML Query Tool - Zero Dependencies',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Logan Smith',
    author_email='contact@metaphy.io',
    url='https://github.com/DonkRonk17/JSONQuery',
    py_modules=['jsonquery'],
    entry_points={
        'console_scripts': [
            'jsonquery=jsonquery:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing',
    ],
    python_requires='>=3.6',
)
