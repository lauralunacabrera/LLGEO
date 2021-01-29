import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()
    
setuptools.setup(
    name = 'llgeo',
    version = '0.0.6',
    author = 'Laura Luna',
    author_email = 'lauralunacabrera@gmail.com',
    description = 'Python library for Geotechnical Engineering',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/lauralunacabrera/LLGEO.git', 

    classifiers = [ 'Programming Language :: Python :: 3',
                    'License :: OSI Approved :: MIT License',
                    'Operating System :: OS Independent',
                      ],

    python_requires = '>=3.6',

    packages = setuptools.find_packages(),

    install_requires = ['numpy      >= 1.16.4' ,
                        'pandas     >= 1.1.5'  ,
                        'scipy      >= 1.2.0'  ,
                        'ezdxf      >= 0.14.2' ,
                        'matplotlib >= 3.0.3'  ,
                        'seaborn    >= 0.9.0'  ,
                        ]

)
