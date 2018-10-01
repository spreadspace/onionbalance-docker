from setuptools import setup

setup(
    name='k8sbalance',
    version='0.0.0',
    description='',
    author='nicoo',
    author_email='nicoo@r3.at',
    url='https://github.com/spreadspace/onionbalance-docker/',
    license='ISC',
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'License :: OSI Approved :: ISC License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    scripts=['k8sbalance.py'],
    python_requires='>=3.6',
)
