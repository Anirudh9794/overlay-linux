from overlay_north import server
from startup import Startup
import sys

if __name__ == '__main__':
    startup = Startup()
    if not startup.start():
        print("\r\nUnable to finish startup. Exiting...")
        exit()

    server.app.run(host='0.0.0.0', port='8081', debug=True)
