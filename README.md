# Poko Bot

Update of the freenove hexapod robot with a Raspberry Pi.

This project's aim is to clean the dirty code made by Freenove.
I also started to improve the thread and simplify the code. 

## Improvements

* Clean the code and avoid duplication
* Remove the useless UI (It was a simple on off button, that's pointless)
* Does not block listening on one IP on wlan0. The server broadcast to any interfaces (0.0.0.0)
* Add config files (video, robot, ...) in yaml format