# (C) British Crown Copyright 2015, Met Office
# 
# This file is part of metarelate.
# 
# metarelate is free software: you can redistribute it and/or 
# modify it under the terms of the GNU Lesser General Public License 
# as published by the Free Software Foundation, either version 3 of 
# the License, or (at your option) any later version.
# 
# metarelate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with metarelate. If not, see <http://www.gnu.org/licenses/>.

from threading import Thread

import metarelate

# maximum number of threads for multi-thrteading code
MAXTHREADS = metarelate.site_config.get('num_workers')

class WorkerThread(Thread):
    """
    A :class:threading.Thread which moves objects from an input queue to an
    output deque using a 'dowork' method, as defined by a subclass.

    """
    def __init__(self, aqueue, adeque, fu_p=None, service=None):
        self.queue = aqueue
        self.deque = adeque
        self.fuseki_process = fu_p
        self.service = service
        Thread.__init__(self)
        self.daemon = True
    def run(self):
        while not self.queue.empty():
            resource = self.queue.get()
            try:
                self.dowork(resource)
                self.deque.append(resource)
            except Exception, e:
                print e
            self.queue.task_done()
