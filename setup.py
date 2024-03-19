from setuptools import setup, find_packages

setup(
    name='image_cleaner',
    version='0.1.0',
    author='csommeregger',
    author_email='christian.sommeregger@gmail.com',
    description='webinterface for cleaning images ',
    packages=find_packages(),
    install_requires=[
        'flask',
        'pydrive2[fsspec]'
        'numpy',
        'logging',
    ],
    include_package_data = True,
    package_data={
        'templates': ['templates/*'],
    },
)