from setuptools import setup
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]

setup(name="minipdb",
      version="0.1",
      description="Small API to expose the Low Response Score from Census",
      author="Gonzalo Rivero",
      author_email="gonzalorivero@westat.com",
      install_requires=reqs)
