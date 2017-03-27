from setuptools import setup
setup(name="minipdb",
      version="0.1",
      description="Small API to expose the Low Response Score from Census",
      author="Gonzalo Rivero",
      author_email="gonzalorivero@westat.com",
      install_requires=[
          'Flask==0.10.1',
          'Flask-SQLAlchemy==1.0'
      ],
)
