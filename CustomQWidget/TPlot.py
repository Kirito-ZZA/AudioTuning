import pyqtgraph as pg
import numpy as np


class TPlot(pg.PlotCurveItem):
    def __init__(self, *args, **kwds):
        self.data = None
        self.limit = 10000  # maximum number of samples to be plotted
        self.scale_k = 1
        self.data, self.pos = None, (0, 1)
        pg.PlotCurveItem.__init__(self, *args, **kwds)

    def setScale(self, k):
        self.scale_k = k

    def setPlotData(self, data, x=None):
        self.data = data
        self._x = x
        self.updatePlot()

    def getFullData(self):
        if self.data is not None:
            return self.data[self.pos[0]:self.pos[1]]
        return None

    def viewRangeChanged(self):
        self.updatePlot()

    def get_val_index(self, val, x):
        l, r = 0, len(x) - 1
        mid = (l + r) // 2
        while (r - l) > 1:
            if x[mid] > val:
                r = mid
            else:
                l = mid
            mid = (l + r) // 2
        return l, x[l]

    def updatePlot(self):
        if self.data is None:
            self.setData([])
            return

        vb = self.getViewBox()
        if vb is None:
            return  # no ViewBox yet

        # Determine what data range must be read from HDF5
        xrange = vb.viewRange()[0]
        if self._x is None:
            start = max(0, int(xrange[0])-1)
            stop = min(len(self.data), int(xrange[1]+2))
        else:
            start, _ = self.get_val_index(max(0, xrange[0]), self._x)
            stop, _ = self.get_val_index(self._x[-1], self._x)

        # Decide by how much we should downsample
        ds = int((stop-start) / self.limit) + 1

        self.pos = (start, stop)
        if ds == 1:
            # Small enough to display with no intervention.
            visible = self.data[start:stop]
            visible_x = self._x[start:stop] if self._x is not None else None
            scale = 1
        else:
            # Here convert data into a down-sampled array suitable for visualizing.
            # Must do this piecewise to limit memory usage.
            if ds % 2 > 0:
                ds += 1
            samples = 1 + ((stop-start) // ds)
            visible = np.zeros(samples*2, dtype=self.data.dtype)
            visible_x = np.zeros(samples*2, dtype=self.data.dtype) if self._x is not None else None
            sourcePtr = start
            targetPtr = 0

            # read data in chunks of ~1M samples
            chunkSize = (1000000//ds) * ds
            while sourcePtr < stop - 1:
                chunk = self.data[sourcePtr:min(stop, sourcePtr+chunkSize)]
                chunk_x = self._x[sourcePtr:min(stop, sourcePtr+chunkSize)] if self._x is not None else None

                sourcePtr += len(chunk)

                # reshape chunk to be integral multiple of ds
                chunk = chunk[:(len(chunk)//ds) * ds].reshape(
                    len(chunk)//ds, ds)
                chunk_x = chunk_x[:(len(chunk_x)//ds) * ds].reshape(
                    len(chunk_x)//ds, ds) if chunk_x is not None else None

                # compute max and min
                chunkMax = chunk.max(axis=1)
                chunkMin = chunk.min(axis=1)

                # interleave min and max into plot data to preserve envelope shape
                visible[targetPtr:targetPtr+chunk.shape[0]*2:2] = chunkMin
                visible[1+targetPtr:1+targetPtr+chunk.shape[0]*2:2] = chunkMax
                if visible_x is not None:
                    visible_x[targetPtr:targetPtr+chunk_x.shape[0]*2] = chunk_x[:,[0, chunk_x.shape[1]//2]].reshape(chunk_x.shape[0]*2)
                targetPtr += chunk.shape[0]*2

            visible = visible[:targetPtr]
            visible_x = visible_x[:targetPtr] if visible_x is not None else None
            scale = ds * 0.5

        if visible_x is not None:
            self.setData(visible_x, visible*self.scale_k)  # update the plot
        else:
            self.setData(visible*self.scale_k)
            self.setPos(start, 0)  # shift to match starting index
            self.resetTransform()
            self.scale(scale, 1)  # scale to match downsampling
