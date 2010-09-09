from setuptools import setup, find_packages
import os

version = '0.1.0'

setup(name='plone.app.z3cformdrafts',
      version=version,
      description="Adds drafts suppurt for z3cforms",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone zc3form drafts',
      author='Jason Mehring',
      author_email='dexterity-development@googlegroups.com',
      url='http://pypi.python.org/pypi/plone.app.z3cformdrafts',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone','plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.dexterity',
          'plone.namedfile',
          'plone.app.drafts',
          'plone.app.textfield',
          'plone.z3cformbuttonoverrides',
          # Zope 2
          'zope.interface',
          'zope.component',
          'z3c.form',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
