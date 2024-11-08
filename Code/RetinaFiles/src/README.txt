The file WebSQController.py contains the Python class WebSQController.
This class contains functions to interact with the Retina WebSQ.

Import this class from that file and create an object using the URL of the WebSQ.

import WebSQController from WebSQController

sq = WebSQController('http://localhost:8080/')
sq.getSettings()

Make sure the file WebSQController.py is in the same folder as your script or change the import path.
The files starting with example_ contain example uses.

The file WebSQController.py contains docstrings for what all the functions do.
There is also provided automated documentation generated from these docstring into a better readable format.

Next to the WebSQController, there is a WebSQSocketController.py file.
This file has two functions to show how to interact with the websockets of the WebSQ.

The WebSQController.py file requires no dependencies
and can run on an old Python interpreter all the way back to Python 2.5,
if you happen to use a very old CentOS box with no root access.
The WebSQSocketController.py file requires minimum 3.6.1 and the websockets package.

This project is licensed under the terms of the MIT license.
Copyright (c) 2023 Single Quantum B. V. and Hielke Walinga
