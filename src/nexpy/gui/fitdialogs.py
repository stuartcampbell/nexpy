#!/usr/bin/env python 
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
# Copyright (c) 2013, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import imp
import logging
import os
import re
import sys

from .pyqt import QtGui, QtCore
import pkg_resources
import numpy as np

from nexusformat.nexus import (NeXusError, NXgroup, NXfield, NXattr,
                               NXroot, NXentry, NXdata, NXparameters)
from .datadialogs import BaseDialog

from ..api.frills.fit import Fit, Function, Parameter

    
class FitDialog(BaseDialog):
    """Dialog to fit one-dimensional NeXus data"""
 
    def __init__(self, entry, parent=None):

        super(FitDialog, self).__init__(parent)
        self.setMinimumWidth(850)        
 
        self.data = self.initialize_data(entry.data)

        from .consoleapp import _tree
        self.tree = _tree

        from .plotview import plotview
        self.plotview = plotview
        self.functions = []
        self.parameters = []

        self.first_time = True
        self.fitted = False
        self.fit = None

        self.initialize_functions()
 
        function_layout = QtGui.QHBoxLayout()
        self.functioncombo = QtGui.QComboBox()
        for name in sorted(self.function_module):
            self.functioncombo.addItem(name)
        self.functioncombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.functioncombo.setMinimumWidth(100)
        add_button = QtGui.QPushButton("Add Function")
        add_button.clicked.connect(self.add_function)
        function_layout.addWidget(self.functioncombo)
        function_layout.addWidget(add_button)
        function_layout.addStretch()
        
        self.header_font = QtGui.QFont()
        self.header_font.setBold(True)

        self.parameter_layout = self.initialize_parameter_grid()

        self.remove_layout = QtGui.QHBoxLayout()
        remove_button = QtGui.QPushButton("Remove Function")
        remove_button.clicked.connect(self.remove_function)
        self.removecombo = QtGui.QComboBox()
        self.removecombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.removecombo.setMinimumWidth(100)
        self.remove_layout.addWidget(remove_button)
        self.remove_layout.addWidget(self.removecombo)
        self.remove_layout.addStretch()

        self.plot_layout = QtGui.QHBoxLayout()
        plot_data_button = QtGui.QPushButton('Plot Data')
        plot_data_button.clicked.connect(self.plot_data)
        plot_function_button = QtGui.QPushButton('Plot Function')
        plot_function_button.clicked.connect(self.plot_model)
        self.plotcombo = QtGui.QComboBox()
        self.plotcombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.plotcombo.setMinimumWidth(100)
        plot_label = QtGui.QLabel('X-axis:')
        self.plot_minbox = QtGui.QLineEdit(str(self.plotview.xtab.axis.min))
        self.plot_minbox.setAlignment(QtCore.Qt.AlignRight)
        plot_tolabel = QtGui.QLabel(' to ')
        self.plot_maxbox = QtGui.QLineEdit(str(self.plotview.xtab.axis.max))
        self.plot_maxbox.setAlignment(QtCore.Qt.AlignRight)
        self.plot_checkbox = QtGui.QCheckBox('Use Data Points')
        self.plot_layout.addWidget(plot_data_button)
        self.plot_layout.addWidget(plot_function_button)
        self.plot_layout.addWidget(self.plotcombo)
        self.plot_layout.addWidget(plot_label)
        self.plot_layout.addWidget(self.plot_minbox)
        self.plot_layout.addWidget(plot_tolabel)
        self.plot_layout.addWidget(self.plot_maxbox)
        self.plot_layout.addWidget(self.plot_checkbox)
        self.plot_layout.addStretch()

        self.action_layout = QtGui.QHBoxLayout()
        fit_button = QtGui.QPushButton("Fit")
        fit_button.clicked.connect(self.fit_data)
        self.fit_label = QtGui.QLabel()
        if self.data.nxerrors:
            self.fit_checkbox = QtGui.QCheckBox('Use Errors')
            self.fit_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.fit_checkbox = QtGui.QCheckBox('Use Poisson Errors')
            self.fit_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.fit_checkbox.stateChanged.connect(self.define_errors)
        self.report_button = QtGui.QPushButton("Show Fit Report")
        self.report_button.clicked.connect(self.report_fit)
        self.save_button = QtGui.QPushButton("Save Parameters")
        self.save_button.clicked.connect(self.save_fit)
        self.restore_button = QtGui.QPushButton("Restore Parameters")
        self.restore_button.clicked.connect(self.restore_parameters)
        self.action_layout.addWidget(fit_button)
        self.action_layout.addWidget(self.fit_label)
        self.action_layout.addStretch()
        self.action_layout.addWidget(self.fit_checkbox)
        self.action_layout.addWidget(self.save_button)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addLayout(function_layout)
        self.layout.addWidget(self.close_buttons())

        self.setLayout(self.layout)

        self.setWindowTitle("Fit NeXus Data")

        self.load_entry(entry)

    def initialize_data(self, data):
        if isinstance(data, NXdata):
            if len(data.nxsignal.shape) > 1:
                raise NeXusError("Fitting only possible on one-dimensional arrays")
            fit_data = NXdata(data.nxsignal, data.nxaxes, title=data.nxtitle)
            if data.nxerrors:
                fit_data.errors = data.nxerrors
            return fit_data
        else:
            raise NeXusError("Must be an NXdata group")

    def initialize_functions(self):

        filenames = set()
        private_path = os.path.join(os.path.expanduser('~'), '.nexpy', 
                                    'functions')
        if os.path.isdir(private_path):
            sys.path.append(private_path)
            for file_ in os.listdir(private_path):
                name, ext = os.path.splitext(file_)
                if name != '__init__' and ext.startswith('.py'):
                    filenames.add(name)
        functions_path = pkg_resources.resource_filename('nexpy.api.frills', 'functions')
        sys.path.append(functions_path)
        for file_ in os.listdir(functions_path):
            name, ext = os.path.splitext(file_)
            if name != '__init__' and ext.startswith('.py'):
                filenames.add(name)
        self.function_module = {}
        for name in sorted(filenames):
            fp, pathname, description = imp.find_module(name)
            try:
                function_module = imp.load_module(name, fp, pathname, description)
            finally:
                if fp:
                    fp.close()
            if hasattr(function_module, 'function_name'):
                self.function_module[function_module.function_name] = function_module

    def initialize_parameter_grid(self):
        grid_layout = QtGui.QVBoxLayout()
        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QtGui.QWidget()

        self.parameter_grid = QtGui.QGridLayout()
        self.parameter_grid.setSpacing(10)
        headers = ['Function', 'Np', 'Name', 'Value', '', 'Min', 'Max', 'Fixed']
        width = [100, 50, 100, 100, 100, 100, 100, 50, 100]
        column = 0
        for header in headers:
            label = QtGui.QLabel()
            label.setFont(self.header_font)
            label.setAlignment(QtCore.Qt.AlignHCenter)
            label.setText(header)
            self.parameter_grid.addWidget(label, 0, column)
            self.parameter_grid.setColumnMinimumWidth(column, width[column])
            column += 1

        scroll_widget.setLayout(self.parameter_grid)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setMinimumHeight(200)
        
        grid_layout.addWidget(scroll_area)

        return grid_layout

    def compressed_name(self, name):
        return re.sub(r'([a-zA-Z]*) # (\d*)', r'\1\2', name)

    def expanded_name(self, name):
        return re.sub(r'([a-zA-Z]*)(\d*)', r'\1 # \2', name)
    
    def parse_function_name(self, name):
        match = re.match(r'([a-zA-Z]*)(\d*)', name)
        return match.group(1), match.group(2)

    def load_entry(self, entry):
        if 'fit' in entry.entries:
            for group in entry.entries:
                name, n = self.parse_function_name(group)
                if name in self.function_module:
                    module = self.function_module[name]
                    parameters = []
                    for p in module.parameters:
                        if p in entry[group].parameters.entries:
                            parameter = Parameter(p)
                            parameter.value = entry[group].parameters[p].nxdata
                            parameter.min = float(entry[group].parameters[p].attrs['min'].nxdata)
                            parameter.max = float(entry[group].parameters[p].attrs['max'].nxdata)                        
                            parameters.append(parameter)
                    f = Function(group, module, parameters, n)
                    self.functions.append(f)
            self.functions = sorted(self.functions)
            for f in self.functions:
                self.add_function_rows(f)
            self.write_parameters()
               
    def add_function(self):
        module = self.function_module[self.functioncombo.currentText()]
        function_index = len(self.functions) + 1
        name = '%s%s' % (module.function_name, str(function_index))
        parameters = [Parameter(p) for p in module.parameters]
        f = Function(name, module, parameters, function_index)
        self.functions.append(f)
        self.index_parameters()
        self.guess_parameters()
        self.add_function_rows(f)
        self.write_parameters()
 
    def index_parameters(self):
        np = 0
        for f in sorted(self.functions):
            for p in f.parameters:
                np += 1
                p.parameter_index = np
    
    def add_function_rows(self, f):
        self.add_parameter_rows(f)
        if self.first_time:
            self.layout.insertLayout(1, self.parameter_layout)
            self.layout.insertLayout(2, self.remove_layout)
            self.layout.insertLayout(3, self.plot_layout)
            self.layout.insertLayout(4, self.action_layout)
            self.plotcombo.addItem('All')
            self.plotcombo.insertSeparator(1)
        self.removecombo.addItem(self.expanded_name(f.name))
        self.plotcombo.addItem(self.expanded_name(f.name))
        self.first_time = False

    def remove_function(self):
        expanded_name = self.removecombo.currentText()
        name = self.compressed_name(expanded_name)
        f = list(filter(lambda x: x.name == name, self.functions))[0]
        for row in f.rows:
            for column in range(8):
                item = self.parameter_grid.itemAtPosition(row, column)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
                        self.parameter_grid.removeWidget(widget)
                        widget.deleteLater()           
        self.functions.remove(f)
        self.plotcombo.removeItem(self.plotcombo.findText(expanded_name))
        self.removecombo.removeItem(self.removecombo.findText(expanded_name))
        del f
        nf = 0
        np = 0
        for f in sorted(self.functions):
            nf += 1
            name = '%s%s' % (f.module.function_name, str(nf))
            self.rename_function(f.name, name)
            f.name = name
            f.label_box.setText(self.expanded_name(f.name))
            for p in f.parameters:
                np += 1
                p.parameter_index = np
                p.parameter_box.setText(str(p.parameter_index))     

    def rename_function(self, old_name, new_name):
        old_name, new_name = self.expanded_name(old_name), self.expanded_name(new_name)
        plot_index = self.plotcombo.findText(old_name)
        self.plotcombo.setItemText(plot_index, new_name)
        remove_index = self.removecombo.findText(old_name)
        self.removecombo.setItemText(remove_index, new_name)
        
    def add_parameter_rows(self, f):        
        row = self.parameter_grid.rowCount()
        name = self.expanded_name(f.name)
        f.rows = []
        f.label_box = QtGui.QLabel(name)
        self.parameter_grid.addWidget(f.label_box, row, 0)
        for p in f.parameters:
            p.parameter_index = row
            p.parameter_box = QtGui.QLabel(str(p.parameter_index))
            p.value_box = QtGui.QLineEdit()
            p.value_box.setAlignment(QtCore.Qt.AlignRight)
            p.error_box = QtGui.QLabel()
            p.min_box = QtGui.QLineEdit('-inf')
            p.min_box.setAlignment(QtCore.Qt.AlignRight)
            p.max_box = QtGui.QLineEdit('inf')
            p.max_box.setAlignment(QtCore.Qt.AlignRight)
            p.fixed_box = QtGui.QCheckBox()
#            p.bound_box = QtGui.QLineEdit()
            self.parameter_grid.addWidget(p.parameter_box, row, 1,
                                          alignment=QtCore.Qt.AlignHCenter)
            self.parameter_grid.addWidget(QtGui.QLabel(p.name), row, 2)
            self.parameter_grid.addWidget(p.value_box, row, 3)
            self.parameter_grid.addWidget(p.error_box, row, 4)
            self.parameter_grid.addWidget(p.min_box, row, 5)
            self.parameter_grid.addWidget(p.max_box, row, 6)
            self.parameter_grid.addWidget(p.fixed_box, row, 7,
                                          alignment=QtCore.Qt.AlignHCenter)
#            self.parameter_grid.addWidget(p.bound_box, row, 8)
            f.rows.append(row)
            row += 1
        self.parameter_grid.setRowStretch(self.parameter_grid.rowCount(),10)

    def read_parameters(self):
        def make_float(value):
            try:
                return float(value)
            except Exception:
                return None
        for f in self.functions:
            for p in f.parameters:
                p.value = make_float(p.value_box.text())
                p.min = make_float(p.min_box.text())
                p.max = make_float(p.max_box.text())
                p.vary = not p.fixed_box.checkState()

    def write_parameters(self):
        for f in self.functions:
            for p in f.parameters:
                if p.parameter_index:
                    p.parameter_box.setText(str(p.parameter_index))
                if p.value:
                    p.value_box.setText('%.6g' % p.value)
                if p.vary and p.stderr:
                    p.error_box.setText('+/- %.6g' % p.stderr)
                else:
                    p.error_box.setText(' ')
                if p.min:
                    p.min_box.setText('%.6g' % p.min)
                if p.max:
                    p.max_box.setText('%.6g' % p.max)

    def guess_parameters(self):
        fit = Fit(self.data, self.functions)
        y = np.array(fit.y)
        for f in self.functions:
            guess = f.module.guess(fit.x, y)
            list(map(lambda p, g: p.__setattr__('value', g), f.parameters, 
                     guess))
            y = y - f.module.values(fit.x, guess)

    def get_model(self, f=None):
        self.read_parameters()
        fit = Fit(self.data, self.functions)
        if self.plot_checkbox.isChecked():
            x = fit.x
        else:
            x = np.linspace(float(self.plot_minbox.text()), 
                            float(self.plot_maxbox.text()), 1001)
        return NXdata(NXfield(fit.get_model(x, f), name='model'),
                      NXfield(x, name=fit.data.nxaxes[0].nxname), 
                      title='Fit Results')
    
    def plot_data(self):
        self.data.plot()

    def plot_model(self):
        plot_function = self.plotcombo.currentText()
        if plot_function == 'All':
            self.get_model().oplot('-')
        else:
            name = self.compressed_name(plot_function)
            f = list(filter(lambda x: x.name == name, self.functions))[0]
            self.get_model(f).oplot('--')

    def define_errors(self):
        if self.fit_checkbox.isChecked():
            self.data.errors = np.sqrt(self.data.nxsignal)

    def fit_data(self):
        self.read_parameters()
        if self.fit_checkbox.isChecked():
            use_errors = True
        else:
            use_errors = False
        from .mainwindow import report_error
        try:
            self.fit = Fit(self.data, self.functions, use_errors)
            self.fit.fit_data()
        except Exception as error:
            report_error("Fitting Data", error)
        if self.fit.result.success:
            self.fit_label.setText('Fit Successful Chi^2 = %s' % self.fit.result.redchi)
        else:
            self.fit_label.setText('Fit Failed Chi^2 = %s' % self.fit.result.redchi)
        self.write_parameters()
        if not self.fitted:
            self.action_layout.addWidget(self.report_button)
            self.action_layout.addWidget(self.restore_button)
            self.save_button.setText('Save Fit')
        self.fitted = True

    def report_fit(self):
        message_box = QtGui.QMessageBox()
        message_box.setText("Fit Results")
        if self.fit.result.success:
            summary = 'Fit Successful'
        else:
            summary = 'Fit Failed'
        if self.fit.result.errorbars:
            errors = 'Uncertainties estimated'
        else:
            errors = 'Uncertainties not estimated'
        text = '%s\n' % summary +\
               '%s\n' % self.fit.result.message +\
               '%s\n' % self.fit.result.lmdif_message +\
               'scipy.optimize.leastsq error value = %s\n' % self.fit.result.ier +\
               'Chi^2 = %s\n' % self.fit.result.chisqr +\
               'Reduced Chi^2 = %s\n' % self.fit.result.redchi +\
               '%s\n' % errors +\
               'No. of Function Evaluations = %s\n' % self.fit.result.nfev +\
               'No. of Variables = %s\n' % self.fit.result.nvarys +\
               'No. of Data Points = %s\n' % self.fit.result.ndata +\
               'No. of Degrees of Freedom = %s\n' % self.fit.result.nfree +\
               '%s' % self.fit.fit_report()
        message_box.setInformativeText(text)
        message_box.setStandardButtons(QtGui.QMessageBox.Ok)
        spacer = QtGui.QSpacerItem(500, 0, 
                                   QtGui.QSizePolicy.Minimum, 
                                   QtGui.QSizePolicy.Expanding)
        layout = message_box.layout()
        layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())
        message_box.exec_()

    def save_fit(self):
        """Saves fit results to an NXentry"""
        self.read_parameters()
        entry = NXentry()
        entry['data'] = self.data
        for f in self.functions:
            entry[f.name] = self.get_model(f)
            parameters = NXparameters()
            for p in f.parameters:
                parameters[p.name] = NXfield(p.value, error=p.stderr, 
                                             initial_value=p.init_value,
                                             min=str(p.min), max=str(p.max))
            entry[f.name].insert(parameters)
        if self.fit is not None:
            entry['title'] = 'Fit Results'
            entry['fit'] = self.get_model()
            fit = NXparameters()
            fit.nfev = self.fit.result.nfev
            fit.ier = self.fit.result.ier 
            fit.chisq = self.fit.result.chisqr
            fit.redchi = self.fit.result.redchi
            fit.message = self.fit.result.message
            fit.lmdif_message = self.fit.result.lmdif_message
            entry['statistics'] = fit
        else:
            entry['title'] = 'Fit Model'
            entry['model'] = self.get_model()
        if 'w0' not in self.tree:
            self.tree.add(NXroot(name='w0'))
        ind = []
        for key in self.tree['w0']:
            try:
                if key.startswith('f'): 
                    ind.append(int(key[1:]))
            except ValueError:
                pass
        if not ind:
            ind = [0]
        name = 'f'+str(sorted(ind)[-1]+1)
        self.tree['w0'][name] = entry

    def restore_parameters(self):
        for f in self.functions:
            for p in f.parameters:
                p.value = p.init_value
                p.stderr = None
        self.fit_label.setText(' ')
        self.write_parameters()
   
    def accept(self):
        super(FitDialog, self).accept()
        
    def reject(self):
        super(FitDialog, self).reject()

    def closeEvent(self, event):
        event.accept()
