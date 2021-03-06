"""
Introduction
-------------

Spectrum class is designed to simplify the unit conversions, interpolation and arithmetic operations of spectrum data in the form of ``y(x)`` or ``y(x)dx``.
When modeling solar cells, we often have to deal with spectrum with different units. For example, the ``x`` of your EQE is in photon energy (eV), but the ``x`` of the illumination spectrum is in wavelength (nm), and you want to multiply them to get Jsc. You then have to convert the ``x`` of EQE into wavelength, reverse the sequence of both ``x`` and ``y``, interpolate either the EQE or the illumination spectrum, convert ``y`` of the illumination spectrum into photon flux, multiply the data and finally run numerical integration to get Jsc. These processes can cause some headache and very error prone. ``Spectrum`` class aims to make these calculations robust and easy.

Spectrum class bundles the data of ``x``, ``y`` and their associated units together into an object. This design may look clumsy at first sight, but this helps reduce many potential errors that could happen when handling the unit conversions of the data. The reason is that the value of ``y`` is often coupled with the unit of ``x``. For example, converting the ``y`` data from energy flux into photon flux requires the values of ``x``.

Design of ``Spectrum`` class
-----------------------------

An instance of ``Spectrum`` class bundles the following key properties of a spectrum y(x):

- ``x_data``: the values of x
- ``y_data``: the values of y
- ``x_unit``: the unit of x (strings), e.g. 'eV', 'nm', 'J' and so on.
- ``y_area_unit`` (optional): use this if the spectrum is something per area, such as sun irradiance (W/m^2), e.g., 'm 2')
- ``is_spec_density``: a boolean value to specify whether the spectrum is y(x)dx. In other words, this should be set to ``True`` if the integration of y(x)dx is a physical quantity. For example, this should be set to ``True`` when dealing with the sun irradiance spectrum because the integration of the sun irradiance spectrum gives the total illumination power. On the other hand, this should be set to ``False`` for spectrum like quantum efficiency or absorption spectrum.
- ``is_photon_flux``: This boolean values specifies whether the spectrum is photon flux.


Access the values in ``Spectrum``
-----------------------------------

One can use ``get_spectrum()`` or ``get_interp_spectrum()`` to accessing the values of x and y in a spectrum. When retrieving the values of spectrum data, the user has to specify the unit for x. Both of these functions will handle the unit conversion and rearrange the order of x and y (say, when converting nm to eV).

``get_spectrum()`` returns the 2xL numpy array of the x and y data.

``get_interp_spectrum()`` returns the 2xL numpy array of interpolated x and y data from given x.


Arithmetic operations
-----------------------

Spectrum class supports arithmetic operations between different spectrum, for example: ::

    # Multiplication of two spectrum
    s3=s1*s2

If s1 and s2 have different x, the function will interpolate s2 based on the values of x in s1.
After that, it does the multiplication of y in s1 and s2.

Spectrum calss also supports arithmetic operations with single float number, for example: ::

    # Multiply a spectrum by a single number
    s2=s1*0.5

or ::

    s2=0.5*s1

This operation multiply all the y values in s1 by 0.5 and return the result to s2.

   Copyright 2017 Kan-Hua Lee, Toyota Technological Institute

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

"""
import numpy as np
import scipy.constants as sc
from pint import UnitRegistry
import copy

ug = UnitRegistry()

# for unit comparision. Declared here for perfomance purpose.
_lu = ug.parse_units('m').dimensionality  # length
_eu = ug.parse_units('J').dimensionality  # energy
_ilu = ug.parse_units('1/m').dimensionality  # 1/length
_itu = ug.parse_units('1/s').dimensionality  # 1/s, frequency

# define constants for unit conversions
_h_unit = ug.parse_expression('J s')
_c_unit = ug.parse_expression('m/s')


def _energy_to_length(value, e_unit, l_unit):
    """
    Convert wavelength to photon energy. The conversion is bi-directional. As a result, instead of using source and destination as input parameters, it uses "energy unit" and "length unit" as inputs.

    :param value: The unit to be converted
    :param e_unit: the unit of energy, such as 'J', 'eV'
    :type e_unit: str
    :param l_unit: the unit of wavelength, such as 'm', 'nm'
    :type l_unit: str
    :return:
    """

    c, h = _energy_to_length_factor(e_unit, l_unit)

    return h * c / value


def _energy_to_length_factor(e_unit, l_unit):
    """
    Convert the units of Planck's constant and speed of light

    :param e_unit:
    :type e_unit: str
    :param l_unit:
    :type l_unit: str
    :return: c,h
    """

    dest_h_u = ug.parse_units('%s s' % e_unit)
    dest_c_u = ug.parse_units('%s/s' % l_unit)
    if dest_h_u.dimensionality != _h_unit.dimensionality:
        raise ValueError("e_unit should be a valid energy unit")
    if dest_c_u.dimensionality != _c_unit.dimensionality:
        raise ValueError('l_unit should be a valid length unit')
    h = ug.convert(sc.h, _h_unit, dest_h_u)
    c = ug.convert(sc.c, _c_unit, dest_c_u)
    return c, h


def _spec_density_conversion(x, y, e_unit, l_unit):
    """
    Convert the units of spectral density.

    :param x: x_data
    :type x: np.ndarray
    :param y: y_data
    :type y: np.ndarray
    :param e_unit: the unit of energy, such as 'J', 'eV'
    :type e_unit: str
    :param l_unit: the unit of wavelength, such as 'm', 'nm'
    :type l_unit: str
    :return: x, y
    """

    c, h = _energy_to_length_factor(e_unit, l_unit)

    new_y = y * c * h / x ** 2

    return x, new_y


def compare_wavelength_dimension(unit_1, unit_2):
    """
    Check whether the unit_1 and unit_2 are valid units.
    It returns true when:

    unit_1==unit_2
    set(unit_1,unit_2)=set([length],[energy])
    set(unit_1,unit_2)=set([length],1/[length])
    set(unit_1,unit_2)=set([length],[frequency])

    :param unit_1: unit 1, e.g. 'm', 'J',etc.
    :type unit_1: str
    :param unit_2: unit 2, e.g. 'm', 'J',etc.
    :type unit_2: str
    :return: boolean value
    :rtype: bool
    """

    un1 = ug.parse_units(unit_1).dimensionality
    un2 = ug.parse_units(unit_2).dimensionality

    if un1 == un2:
        return True
    elif set([un1, un2]) == set([_lu, _eu]):
        return True
    elif set([un1, un2]) == set([_lu, _ilu]):
        return True
    elif set([un1, un2]) == set([_lu, _itu]):
        return True
    else:
        return False


class Spectrum(object):
    """
    This class handles the operation of the spectrum y(x), including unit conversion and multiplication.


    It can handle unit conversions of different types of spectrum, including:

    - Standard spectrum. The unit of y is independent of x, e.g. quantum efficiency, absorption spectrum, etc.
    - Sepctral density. The unit of y is per [x-unit]. For example, the Black-body radiation spectrum is often in the unit of energy/nm/m^2
    - Photon flux: y is number of photons. When converting y into energy (J), it has to be multiplied by its photon energy.

    """

    def __init__(self, x_data, y_data, x_unit, y_unit="", is_spec_density=False, is_photon_flux=False):
        """
        Constructor of the spectrum y(x)

        :param is_spec_density:
        :param x_data: x data of the spectrum (1d numpy array)
        :param y_data: y data of the spectrum (1d numpy array)
        :param x_unit: the unit of x (string), e.g. 'nm', 'eV'
        :param y_unit: (string) If y is per area, put area unit here, e.g. 'm-2' or 'cm-2'.
                Put null string '' if y does not have area unit
        :param is_photon_flux: (boolean). True if y is number of photons.
        """

        # TODO: fix docstring's y unit
        self.set_spectrum(x_data=x_data, y_data=y_data, x_unit=x_unit,
                          y_area_unit=y_unit,
                          is_photon_flux=is_photon_flux,
                          is_spec_density=is_spec_density)

    def set_spectrum(self, x_data, y_data, x_unit, y_area_unit, is_photon_flux, is_spec_density):
        """
        This is essentially a constructor method that sets up the attributes of the object.
        It converts everything to standard MKS unit. x_data: 'm', y_data: '[]/m^2-m'

        :param x_data: x data of the spectrum (1d numpy array)
        :param y_data: y data of the spectrum (1d numpy array)
        :param x_unit: the unit of x (string), e.g. 'nm', 'eV'
        :type x_unit: str
        :param y_area_unit: If y is per area, put area unit here, e.g. 'm**-2' or 'cm**-2'. Put null string '' if y does not have area unit
        :type y_area_unit: str
        :param is_photon_flux: True if y is number of photons.
        :type is_photon_flux: bool
        :param is_spec_density: True if y is spectral density.
        :type is_spec_density: bool
        :return: None
        """

        assert isinstance(x_data, np.ndarray)
        assert isinstance(y_data, np.ndarray)
        assert isinstance(x_unit, str)
        assert isinstance(y_area_unit, str)
        assert isinstance(is_photon_flux, bool)
        assert isinstance(is_spec_density, bool)

        # Convert everything to photon energy : [arb]/m^2-m

        self.is_spec_density = is_spec_density

        if y_area_unit != '':
            self.core_x, self.core_y = self.convert_spectrum_unit(x_data, y_data, from_x_unit=x_unit, to_x_unit='m',
                                                                  from_y_area_unit=y_area_unit, to_y_area_unit='m**-2',
                                                                  is_spec_density=self.is_spec_density)
            self.y_area_unit = 'm**-2'
        else:
            self.core_x, self.core_y = self.convert_spectrum_unit(x_data, y_data, from_x_unit=x_unit, to_x_unit='m',
                                                                  from_y_area_unit='', to_y_area_unit='',
                                                                  is_spec_density=self.is_spec_density)
            self.y_area_unit = ''

        # Convert photon flux to energy (J) representation
        if is_photon_flux:
            self.core_y = self._as_energy(self.core_x, self.core_y)

    def convert_spectrum_unit(self, x_data, y_data, from_x_unit, to_x_unit,
                              from_y_area_unit, to_y_area_unit,
                              is_spec_density):

        """
        A general method for converting the spectrum y(x) from one set of unit to another.
        Note that this only supports the conversion of x from:
        [length]<->[frequency]
        [length]<-> 1/[length]
        [length]<->[energy]

        This is because Spectrum class converts the units of x to [length] first when initilizing or new spectrum is set.
        Therefore this function only implments the bi-direction unit conversions that involves [length].

        :param x_data: data of x (numpy array)
        :param y_data: data of y (numpy array)
        :param from_x_unit: the unit of x_data
        :param to_x_unit: the unit of x_data to be converted to
        :param from_y_area_unit: the unit of area of y_data
        :param to_y_area_unit: the unit of area of y_data tobe converted to
        :param is_spec_density: True if the data is spectral density.
        :return: a tuple of 1-d array (new_x_data, new_y_data)
        """

        assert isinstance(x_data, np.ndarray)
        assert isinstance(y_data, np.ndarray)
        assert isinstance(from_x_unit, str)
        assert isinstance(to_x_unit, str)
        assert isinstance(from_y_area_unit, str)
        assert isinstance(to_y_area_unit, str)
        assert isinstance(is_spec_density, bool)

        src_x_u = ug.parse_units(from_x_unit)
        des_x_u = ug.parse_units(to_x_unit)

        src_x_udim = src_x_u.dimensionality
        des_x_udim = des_x_u.dimensionality

        au1 = ug.parse_units(from_y_area_unit)
        au2 = ug.parse_units(to_y_area_unit)

        if x_data.size != y_data.size:
            raise ValueError("The array size of x_data and y_data do not match.")

        if not compare_wavelength_dimension(from_x_unit, to_x_unit):
            raise ValueError("The dimension of from_x_unit and to_x_unit do not match.")

        if not au1.dimensionality == au2.dimensionality:
            raise ValueError("The dimension of from y_area_unit and to_y_area_unit do not match.")

        if is_spec_density:
            from_dx_unit = from_x_unit + "**-1"
            to_dx_unit = to_x_unit + "**-1"
        else:
            from_dx_unit = ""
            to_dx_unit = ""

        orig_y_div_unit = from_y_area_unit + " " + from_dx_unit
        new_orig_y_div_unit = to_y_area_unit + " " + to_dx_unit

        # Simple case
        if src_x_udim == des_x_udim:

            new_x_data = ug.convert(x_data, ug.parse_units(from_x_unit), ug.parse_units(to_x_unit))

            if is_spec_density:
                new_y_data = ug.convert(y_data, ug.parse_units(orig_y_div_unit),
                                        ug.parse_units(new_orig_y_div_unit))
            else:
                if from_y_area_unit != '' and to_y_area_unit != '':
                    new_y_data = ug.convert(y_data, au1, au2)

                else:
                    new_y_data = y_data

        elif src_x_udim == _lu and des_x_udim == _eu:

            new_x_data = _energy_to_length(x_data, to_x_unit, from_x_unit)

            new_y_data = ug.convert(y_data, au1, au2)

            if is_spec_density:
                new_x_data, new_y_data = _spec_density_conversion(new_x_data, new_y_data, to_x_unit, from_x_unit)

        elif src_x_udim == _eu and des_x_udim == _lu:

            new_x_data = _energy_to_length(x_data, from_x_unit, to_x_unit)

            new_y_data = ug.convert(y_data, au1, au2)

            if is_spec_density:
                new_x_data, new_y_data = _spec_density_conversion(new_x_data, new_y_data, from_x_unit, to_x_unit)

        elif set([src_x_udim, des_x_udim]) == set([_lu, _ilu]):

            # The conversion is bi-directional, we use nm -> cm^-1 as the example for the following comments

            x_data_q = x_data * src_x_u  # attach the unit to the quantities

            inv_scr_x_u = 1 / src_x_u  # get the inverse unit of x for converting y, nm -> nm-1

            x_data_q = 1 / x_data_q  # Do the inverse of x data and its unit

            new_x_data = x_data_q.to(des_x_u).m  # Do the unit conversion and retrieve the value

            new_y_data = ug.convert(y_data, au1, au2)

            if is_spec_density:
                # Convert the values of y, for example, from  []/nm to []/cm, assuming that we are converting x from [nm] to [cm]
                new_y_data = ug.convert(new_y_data, inv_scr_x_u, des_x_u)

                # Then run dk=d(lambda)/lambda^2
                new_y_data = new_y_data / new_x_data ** 2

        elif src_x_udim == _lu and des_x_udim == _itu:

            c = ug.convert(sc.c, 'm/s', from_x_unit + ' ' + to_x_unit)

            new_x_data = c / x_data

            new_y_data = ug.convert(y_data, au1, au2)

            if is_spec_density:
                new_y_data = new_y_data * c / new_x_data ** 2

        elif src_x_udim == _itu and des_x_udim == _lu:

            c = ug.convert(sc.c, 'm/s', to_x_unit + ' ' + from_x_unit)

            new_x_data = c / x_data

            new_y_data = ug.convert(y_data, au1, au2)

            if is_spec_density:
                new_y_data = new_y_data * c / new_x_data ** 2

        return new_x_data, new_y_data

    def get_spectrum(self, to_x_unit, to_y_area_unit=None, to_photon_flux=False):
        """
        Retrieve the values of the spectrum based on the given units of x and y.

        :param to_x_unit: the unit of x
        :param to_y_area_unit: the unit of area of y. Default is the y_area_unit of the object.
        :param to_photon_flux: True if converting y to photon flux.
        :return: a 2xL numpy array
        """

        if to_y_area_unit is None:
            to_y_area_unit = self.y_area_unit

        x_data, y_data = self.convert_spectrum_unit(self.core_x, self.core_y,
                                                    from_x_unit='m', to_x_unit=to_x_unit,
                                                    from_y_area_unit=self.y_area_unit, to_y_area_unit=to_y_area_unit,
                                                    is_spec_density=self.is_spec_density)

        # convert the spectrum to photon flux if necessary
        if to_photon_flux:
            y_data = self._as_photon_flux(self.core_x, y_data)

        # Sort the spectrum by wavelength
        sorted_idx = np.argsort(x_data)
        x_data = x_data[sorted_idx]
        y_data = y_data[sorted_idx]

        return np.vstack((x_data, y_data))

    def get_interp_spectrum(self, to_x_data, to_x_unit, to_y_area_unit=None, to_photon_flux=False, interp_left=None,
                            interp_right=None, raise_error=True):

        """
        Get interpolated spectrum.

        :param raise_error: if to_x_data is not within the range of the spectru, raise ValueError
        :param to_x_data: (ndarray) x values to be interpolated
        :param to_x_unit: (string) unit of x of the output value
        :param to_y_area_unit: (string) unit of area of y of the output value.
        :param to_photon_flux: (bool) True if converting the value to photon flux as the output
        :param interp_left: value to return for x < core_x[0], return core_x[0] if set to be None
        :param interp_right: value to return for x> core_x[-1], return core_y[-1] if set to be None
        :return: a 2xL array
        """

        orig_spectrum = self.get_spectrum(to_x_unit, to_y_area_unit, to_photon_flux=to_photon_flux)

        if np.min(to_x_data) < orig_spectrum[0, 0] or np.max(to_x_data) > orig_spectrum[0, -1]:
            if raise_error == True:
                raise ValueError("The interped value is out of bound")

        output_spectrum = np.zeros((2, to_x_data.shape[0]))

        output_spectrum[0, :] = to_x_data
        output_spectrum[1, :] = np.interp(to_x_data, orig_spectrum[0, :],
                                          orig_spectrum[1, :], left=interp_left, right=interp_right)

        return output_spectrum

    def __add__(self, s2):

        return self._arith_op(s2, np.add)

    def __sub__(self, s2):

        return self._arith_op(s2, np.subtract)

    def __truediv__(self, s2):

        return self._arith_op(s2, np.divide)

    def __mul__(self, s2):

        return self._arith_op(s2, np.multiply)

    def __radd__(self, s2):

        return self._arith_op(s2, np.add)

    def __rsub__(self, s2):

        return self._arith_op(s2, np.subtract) * (-1)

    def __rmul__(self, s2):

        return self._arith_op(s2, np.multiply)

    def __rtruediv__(self, s2):

        return self._inverse()._arith_op(s2, np.multiply)

    def _inverse(self):

        if self.y_area_unit != '':
            print("Warning: y data is not dimensionless!")

        newobj = copy.deepcopy(self)
        newobj.core_y = 1 / newobj.core_y

        return newobj

    def _arith_op(self, s2, op):
        """
        Do the arithmetic operations

        :param s2: an instance of Spectrum
        :type s2: Spectrum,float
        :param op: numpy ufunc, such as np.add, np.substract, np.multiply, np.divide
        :return: the new Spectrum instance.
        """

        if isinstance(s2, Spectrum):
            return self._spec_arith_op(s2, op, inplace=False)

        else:
            try:
                newobj = copy.deepcopy(self)
                newobj.core_y = op(newobj.core_y, s2)

                if newobj.core_x.shape != newobj.core_y.shape:
                    raise Exception("The multipler should either be a scalar or a Spectrum calss object"
                                    ", or an ndarray that matches the length of the spectrum")

                return newobj
            except (TypeError, AttributeError) as err:
                raise err(
                    "Runtime Error: The multipler should either be a scalar or a Spectrum class object when doing Spectrum multiplication")

    def _spec_arith_op(self, s2, op, inplace=True):
        """
        Do the arithmetic operations of two Spectrum instances

        :param s2: an instance of Spectrum
        :type s2: Spectrum
        :param op: numpy ufunc, such as np.add, np.substract, np.multiply, np.divide
        :param inplace: True if the results overwrites the instance itself.
        :type inplace: bool
        :return: the new spectrum opject. Return None if inplace is set True
        """

        assert isinstance(s2, Spectrum)

        new_spec = s2.get_interp_spectrum(self.core_x, 'm')

        new_core_spec = op(self.core_y, new_spec[1, :])

        if inplace:
            self.core_y = new_core_spec
            return None
        else:
            newobj = copy.deepcopy(self)
            newobj.core_y = new_core_spec
            return newobj

    def _as_photon_flux(self, wavelength, energy_flux):
        return energy_flux / (sc.h * sc.c) * wavelength

    def _as_energy(self, wavelength, photon_flux):
        return photon_flux * (sc.h * sc.c) / wavelength

    def rsum(self):
        """
        Integration of the spectrum, i.e., \int y(x)dx
        Internally, it simply does np.trapz(y,x)

        :return:  The integrated value.
        """

        if self.is_spec_density == False:
            raise ArithmeticError("This spectrum instance is not integrable, since self.is_spec_density is false")

        else:
            return np.trapz(self.core_y, self.core_x)

    def cut(self, start, end, unit):
        """
        Cut a particular band of spectrum y(x), where start<x<end

        :param start: the starting x
        :param end: the end x
        :param unit: the unit of x
        :return: a new spectrum
        """

        bound_sp = self.get_interp_spectrum(to_x_data=np.array([start, end]), to_x_unit=unit)

        center_sp = self.get_spectrum(to_x_unit=unit)

        center_sp = center_sp[:, center_sp[0, :] >= start]
        center_sp = center_sp[:, center_sp[0, :] <= end]

        c_sp = np.hstack((bound_sp, center_sp))

        # Sort the spectrum by wavelength
        sorted_idx = np.argsort(c_sp[0, :])
        c_sp = c_sp[:, sorted_idx]

        new_spec = copy.deepcopy(self)

        new_spec.set_spectrum(c_sp[0, :], c_sp[1, :], x_unit=unit, y_area_unit=self.y_area_unit,
                              is_spec_density=self.is_spec_density,
                              is_photon_flux=False)

        return new_spec


if __name__ == "__main__":
    pass
