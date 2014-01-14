#-----------------------------------------------------------------------------
# Copyright (c) 2013, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------
"""
Module to read in a SPEC file and convert it to NeXus.

Each importer needs to layout the GUI buttons necessary for defining the imported file 
and its attributes and a single module, get_data, which returns an NXroot or NXentry
object. This will be added to the NeXpy tree.

Two GUI elements are provided for convenience:

    ImportDialog.filebox: Contains a "Choose File" button and a text box. Both can be 
                          used to set the path to the imported file. This can be 
                          retrieved as a string using self.get_filename().
    ImportDialog.buttonbox: Contains a "Cancel" and "OK" button to close the dialog. 
                            This should be placed at the bottom of all import dialogs.
"""

from PySide import QtCore, QtGui

import numpy as np                  #@UnusedImport
import os                           #@UnusedImport
from nexpy.api.nexus import *       #@UnusedWildImport
from nexpy.gui.importdialog import BaseImportDialog

filetype = "SPEC File"
motors = {'tth': 'two_theta', 'th': 'theta', 'chi': 'chi', 'phi': 'phi',
          'ts1': 'top_slit1', 'bs1': 'bot_slit1'}

#def capitalize(line):
#    return ' '.join([s[0].upper() + s[1:] for s in line.split(' ')])

def lower(text):
    """
    Return standard motors in lower case but leave others unchanged.
    
    The rationale is that some SPEC variables require capitalization,
    e.g., 'NaI'
    """
    if text.lower() in motors.values():
        return text.lower()
    else:
        return text

def reshape_data(scan_data, scan_shape):
    scan_size = np.prod(scan_shape)
    if scan_data.size == scan_size:
        data = scan_data
    else:
        data = np.empty(scan_size)
        data.fill(np.NaN)
        data[0:scan_data.size] = scan_data
    return data.reshape(scan_shape)
                
class ImportDialog(BaseImportDialog):
    """Dialog to import SPEC Scans"""
 
    def __init__(self, parent=None):

        super(ImportDialog, self).__init__(parent)
        
        self.layout = QtGui.QVBoxLayout()
        self.layout.addLayout(self.filebox())
        self.layout.addLayout(self.scanbox())
        self.layout.addWidget(self.buttonbox())
        self.setLayout(self.layout)
  
        self.setWindowTitle("Import "+str(filetype))
        self._support = None    # set in self.chooseFile()
 
    def scanbox(self):
        scanbox = QtGui.QHBoxLayout()
        scanminlabel = QtGui.QLabel("Min. Scan")
        self.scanmin = QtGui.QLineEdit()
        self.scanmin.setFixedWidth(100)
        self.scanmin.setAlignment(QtCore.Qt.AlignRight)
        scanmaxlabel = QtGui.QLabel("Max. Scan")
        self.scanmax = QtGui.QLineEdit()
        self.scanmax.setFixedWidth(100)
        self.scanmax.setAlignment(QtCore.Qt.AlignRight)
        scanbox.addWidget(scanminlabel)
        scanbox.addWidget(self.scanmin)
        scanbox.addWidget(scanmaxlabel)
        scanbox.addWidget(self.scanmax)
        return scanbox

    def choose_file(self):
        """
        Opens a file dialog and sets the file text box to the chosen path
        """
        import pkg_resources
        try:
            pkg_resources.require("pyspec>=" + '0.2')
            from pyspec.spec import SpecDataFile
            self._support = 'pySpec'
            self.get_data = self.get_data__pySpec
        except pkg_resources.DistributionNotFound:
            # fallback support
            from nexpy.api.prjPySpec import SpecDataFile
            self._support = 'prjPySpec'
            self.get_data = self.get_data__prjPySpec
        dirname = self.get_default_directory(self.filename.text())
        filename, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', dirname)
        if os.path.exists(filename):
            self.filename.setText(str(filename))
            self.SPECfile = SpecDataFile(self.get_filename())
            self.set_default_directory(os.path.dirname(filename))
            if self._support == 'pySpec':
                self.spectra = self.SPECfile.findex.keys()
                self.scanmin.setText(str(self.spectra[0]))
                self.scanmax.setText(str(self.spectra[-1]))
            elif self._support == 'prjPySpec':
                self.spectra = self.SPECfile.scans.keys()
                self.scanmin.setText(str(self.SPECfile.getMinScanNumber()))
                self.scanmax.setText(str(self.SPECfile.getMaxScanNumber()))

    def get_spectra(self):
        '''
        PySpec interface: reads specmin & specmax from dialog widgets
        '''
        try:
            specrange = sorted([int(self.scanmin.text()), int(self.scanmax.text())])
            specmin = self.spectra.index(specrange[0])
            specmax = self.spectra.index(specrange[1]) + 1
            return specmin, specmax
        except ValueError, error_message:
                QtGui.QMessageBox.critical(
                    self, "Invalid spectra", str(error_message),
                    QtGui.QMessageBox.Ok, QtGui.QMessageBox.NoButton)

    def get_data__pySpec(self):
        root = NXroot()
        self.import_file = self.get_filename()
        specmin, specmax = self.get_spectra()
        for i in self.spectra[0:specmax]:
            scan = self.SPECfile.getScan(i)
            if i < self.spectra[specmin]:
                continue
            title, entry, scan_type, cols, axis = self.parse_scan(scan)
            root[entry] = NXentry()
            root[entry].title = title
            root[entry].comments = scan.comments
            root[entry].data = NXdata()
            if isinstance(axis,list):
                scan_shape = (axis[1][1].size, axis[0][1].size)
                scan_size = np.prod(scan_shape)
                j = 0
                for col in cols:
                    root[entry].data[col] = NXfield(reshape_data(scan.data[:,j], 
                                                                 scan_shape))
                    j += 1
            else:
                j = 0
                for col in cols:
                    root[entry].data[col] = NXfield(scan.data[:,j])
                    j += 1
            root[entry].data.nxsignal = root[entry].data[cols[-1]]
            root[entry].data.errors = NXfield(np.sqrt(root[entry].data.nxsignal))
            if isinstance(axis,list):
                root[entry].data[axis[0][0]] = axis[0][1]
                root[entry].data[axis[1][0]] = axis[1][1]
                root[entry].data.nxaxes = [root[entry].data[axis[1][0]],
                                           root[entry].data[axis[0][0]]]
            else:
                root[entry].data.nxaxes = root[entry].data[axis]
        return root

    def parse_scan(self, scan):
        '''
        PySpec interface: interprets what type of scan
        '''
        title = scan.header.splitlines()[0]
        words = title.split()
        scan_number = 's%s' % words[1]
        scan_type = words[2]
        cols = [lower(col.replace(' ', '_')) for col in scan.cols]
        axis = cols[0]
        try:
            if scan_type == "hscan":
                axis = 'H'
            elif scan_type == "kscan":
                axis = 'K'
            elif scan_type == "lscan":
                axis = 'L'
            elif scan_type == "hklscan":
                Hstart, Hend, Kstart, Kend, Lstart, Lend = words[3:8]
                if Hstart <> Hend:
                    axis = 'H'
                elif Kstart <> Kend:
                    axis = 'K'
                else:
                    axis = 'L'
            elif scan_type == "hklmesh":
                Q0, Q0start, Q0end, NQ0 = words[3], float(words[4]), float(words[5]), int(words[6])+1
                Q1, Q1start, Q1end, NQ1 = words[7], float(words[8]), float(words[9]), int(words[10])+1
                axis = [(Q0, np.linspace(Q0start, Q0end, NQ0)),
                        (Q1, np.linspace(Q1start, Q1end, NQ1))]                
            else:
                if words[3] in motors.keys():
                    axis = motors[words[3]]
        finally:
            return title, scan_number, scan_type, cols, axis

    def get_data__prjPySpec(self):
        '''
        convert scans from chosen SPEC file into NXroot object and structure
        
        called from mainwindow.MainWindow.import_data() after clicking <Ok> in dialog
        
        Each scan in the range from self.scanmin to self.scanmax (inclusive)
        will be converted to a NXentry.  Scan data will go in a NXdata where 
        the signal=1 is the last column and the corresponding axes= is the first column.
        '''
        scanmin, scanmax = self._get_min_max()
        scanlist = [key for key in self.SPECfile.scans.keys() if scanmin <= key <= scanmax]
        
        root = NXroot()
        self.import_file = self.get_filename()
        for key in scanlist:
            scan = self.SPECfile.getScan(key)
            entry = NXentry()
            entry.title = str(scan)
            entry.date = scan.date
            entry.command = scan.scanCmd
            entry.comments = '\n'.join(scan.comments)

            # store the scan data
            entry.data = NXdata()
            for column in scan.L:
                entry.data[column] = NXfield(scan.data[column])
            
            entry.data.nxsignal = entry.data[scan.column_last]      # primary Y axis
            entry.data.nxaxes = entry.data[scan.column_first]       # primary X axis

            # store the positioner data
            entry.positioners = NXnote()
            for key, value in scan.positioner.items():
                entry.positioners[key] = NXfield(value)

            # store the "float" (H & V) UNICAT-style metadata
            if len(scan.float) > 0:
                entry.metadata = NXnote()
                for key, value in scan.float.items():
                    entry.metadata[key] = NXfield(value)

            # scan.G & scan.T
            entry.spec = NXnote()
            entry.spec['G'] = NXfield(scan.G)
            entry.spec['T'] = NXfield(scan.T)

            root['entry_' + str(key)] = entry
        return root
    
    def _get_min_max(self):
        '''validate and return int(min) and int(max) from the dialog box'''
        try:
            scanmin = int(self.scanmin.text())
        except ValueError, err:
            QtGui.QMessageBox.critical(
                self, "Min must be a number", 
                str(err) + '\n Must specify a scan number in the file',
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.NoButton)
            return None, None

        try:
            scanmax = int(self.scanmax.text())
        except ValueError, err:
            QtGui.QMessageBox.critical(
                self, "Max must be a number", 
                str(err) + '\n Must specify a scan number in the file',
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.NoButton)
            return None, None
        
        if self.SPECfile.getScan(scanmin) is None:
            QtGui.QMessageBox.critical(
                self, "Minimum scan number not found!", 
                self.scanmin.text() + ' is not a scan number in this file',
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.NoButton)
            scanmin = None
        
        if self.SPECfile.getScan(scanmax) is None:
            QtGui.QMessageBox.critical(
                self, "Maximum scan number not found!", 
                self.scanmin.text() + ' is not a scan number in this file',
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.NoButton)
            scanmax = None
        
        return scanmin, scanmax
