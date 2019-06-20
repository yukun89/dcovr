from setuptools import setup

setup(name='dcovr',
      version='0.1',
      description='A tool to generate delta code coverage report',
      url='https://github.com/yukun89/dcovr',
      author='yukun89',
      author_email='huangyukun2012@163.com',
      license='MIT',
      packages=['dcovr'],
      package_dir={'dcovr': 'dcovr'},
      package_data={'dcovr': ['templates/*.html']},
      scripts=['dcovr/scripts/dcov'],
      zip_safe=False)
