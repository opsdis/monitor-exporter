from os.path import dirname, join
from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

def read(fname):
    return open(join(dirname(__file__), fname)).read()


setup(
    name='monitor-exporter',
    version_config={
        "template": "{tag}",
        "dev_template": "{tag}.dev{ccount}",
        "dirty_template": "{tag}.post{ccount}+git.{sha}.dirty",
        "starting_version": "0.0.1",
        "version_callback": None,
        "version_file": None,
        "count_commits_from_version_file": False,
        "branch_formatter": None
    },
    setup_requires=['setuptools-git-versioning'],
    packages=find_packages(),
    author='thenodon',
    author_email='anders@opsdis.com',
    url='https://github.com/opsdis/monitor-exporter',
    license='GPLv3',
    include_package_data=True,
    zip_safe=False,
    description='A Prometheus exporter for OP5 Monitor',
    install_requires=read('requirements.txt').split(),
    python_requires='>=3.6',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
