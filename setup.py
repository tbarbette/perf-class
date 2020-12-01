import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="perf-class",
    version="1.0.2",
    author="Tom Barbette",
    author_email="t.barbette@gmail.com",
    description="A tool to mep perf script events to classes of events using regex",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tbarbette/perf-class",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Operating System Kernels :: Linux",
    ],
    python_requires='>=3.6',
    entry_points = {
              'console_scripts': [
                  'perf-class=perf_class.perf_class:perfclass',
              ],
          },
)
