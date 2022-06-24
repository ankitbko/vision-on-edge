# Object detection Sample Application

The sample provided is an implementation of the above design discussed in blog posts. [TODO: Link to blog posts](http://LINK).

## Running the sample

### Prerequisite

To execute the sample, the developer machine must have either -

* [Visual Studio Code](https://code.visualstudio.com/)
* [Docker](https://docs.docker.com/engine/install/)

OR

* [Python 3.9](https://www.python.org/downloads/release/python-390/)

### Steps

1. Clone the repository.
1. Prepare environment.
    1. If using Docker and Visual Studio Code, open the repository in [Visual Studio Code Remote - Containers](https://code.visualstudio.com/docs/remote/containers) following this [guide](https://code.visualstudio.com/docs/remote/containers#_reopen-folder-in-container)
    1. Or in case of using Python, install the [required packages](../code/requirements.txt) using [pip](https://pip.pypa.io/en/stable/)
1. Run command `python main.py` from *multiprocessing* to start the sample.
1. The video feed will be shown in User Interface, via ULR [http://localhost:7001/](http://localhost:7001/).
1. The time taken by the ML model to process the frame will be shown in the Console.
