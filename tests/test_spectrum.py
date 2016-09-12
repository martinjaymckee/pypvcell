__author__ = 'kanhua'

import unittest
import numpy as np
from spectrum import Spectrum
import scipy.constants as sc
from units_system import UnitsSystem
from photocurrent import gen_square_qe
from illumination import illumination
import matplotlib.pyplot as plt

us = UnitsSystem()


class SpectrumTestCases(unittest.TestCase):
    def setUp(self):
        # set up cases for length wavelength conversions
        self.init_wl = np.linspace(300, 1000, num=5)
        self.init_spec = np.ones((self.init_wl.shape[0],))
        self.spec_base = Spectrum(self.init_wl, self.init_spec, "nm", "m-2")

        # set up cases
        self.init_wl2 = np.linspace(1, 5, num=1000)
        self.init_spec2 = np.linspace(1, 5, num=1000)
        self.spec_base2 = Spectrum(self.init_wl2, self.init_spec2, area_unit="m-2", wavelength_unit="eV")

    def test_1(self):
        spectrum = self.spec_base.get_spectrum_density("m-2", "nm")
        assert np.all(np.isclose(spectrum[0, :], self.init_wl))
        assert np.all(np.isclose(spectrum[1, :], self.init_spec))

    def test_2(self):
        spectrum = self.spec_base.get_spectrum_density("cm-2", 'nm')
        assert np.all(np.isclose(spectrum[0, :], self.init_wl))
        assert np.all(np.isclose(spectrum[1, :], self.init_spec / 1e4))

    def test_3(self):
        spectrum = self.spec_base.get_spectrum_density("cm-2", 'm')
        assert np.all(np.isclose(spectrum[0, :], self.init_wl / 1e9))
        assert np.all(np.isclose(spectrum[1, :], self.init_spec / 1e4 * 1e9))

    def test_4(self):
        spectrum = self.spec_base2.get_spectrum_density("m-2", 'nm')

        assert np.all(np.isclose(spectrum[0, :], np.sort(us.eVnm(self.init_wl2))))
        assert np.isclose(np.trapz(spectrum[1, :], spectrum[0, :]), np.trapz(self.init_spec2, self.init_wl2))

    def test_5(self):
        spectrum = self.spec_base2.get_spectrum_density("m-2", 'J')

        assert np.all(np.isclose(spectrum[0, :], np.sort(self.init_wl2) * sc.e))
        assert np.isclose(np.trapz(spectrum[1, :], spectrum[0, :]), np.trapz(self.init_spec2, self.init_wl2))

    def test_6(self):
        init_wl = np.linspace(1, 5, num=10)
        init_spec = np.ones(init_wl.shape)

        test_spec_base = Spectrum(wavelength=init_wl, spectrum=init_spec, wavelength_unit='eV')
        spectrum = test_spec_base.get_spectrum('nm')

        assert np.all(np.isclose(spectrum[0, :], np.sort(us.eVnm(init_wl))))

    def test_7(self):
        """
        This test converts photon flux to energy flux

        """
        init_wl = np.linspace(300, 500, num=10)
        init_spec = np.ones(init_wl.shape)

        test_spec_base = Spectrum(init_wl, init_spec, wavelength_unit='nm', is_photon_flux=True)
        spectrum = test_spec_base.get_spectrum('nm')

        # Prepare an expected spectrum for comparsion
        expect_spec = init_spec * sc.h * sc.c / us.siUnits(init_wl, 'nm')

        # Since the values of the spectrum are very small, causing the errors in np.isclose()
        # ( both are in the order of ~1e-19) Need renormalise them for proper comparison.
        assert np.all(np.isclose(spectrum[1, :] * 1e19, expect_spec * 1e19))

    def test_8(self):
        """
        This test converts energy flux to photons

        """
        init_wl = np.linspace(300, 500, num=10)
        init_spec = np.ones(init_wl.shape)

        test_spec_base = Spectrum(init_wl, init_spec, 'nm', is_photon_flux=False)
        spectrum = test_spec_base.get_spectrum('nm', flux="photon")

        expect_spec = init_spec / (sc.h * sc.c / us.siUnits(init_wl, 'nm'))

        assert np.all(np.isclose(spectrum[1, :], expect_spec))

    def test_9(self):
        """
        This test sets up a spectrum, and filter it with GaAs substrate.
        Unfiltered part of the spectrum has 10% loss.
        This essentially cut the spectrum at 1.42 eV
        :return:
        """

        sq_qe = gen_square_qe(1.42, 0.9)
        test_ill = illumination()
        # test_qef = qe_filter(sq_qe)

        filtered_ill = test_ill * sq_qe

        assert isinstance(filtered_ill, illumination)

        plt.plot(filtered_ill.get_spectrum('eV')[0, :], filtered_ill.get_spectrum('eV')[1, :], label="filtered")
        plt.plot(test_ill.get_spectrum('eV')[0, :], test_ill.get_spectrum('eV')[1, :], label="original")

        plt.xlabel('wavelength (eV)')
        plt.ylabel('spectrum (W/eV/m^2)')

        plt.legend()

        plt.show()

    def test_mul_scalar(self):
        init_wl = np.linspace(300, 500, num=10)
        init_spec = np.ones(init_wl.shape)

        test_spec_base = Spectrum(init_wl, init_spec, 'nm', is_photon_flux=False)
        test_spec_base=test_spec_base*0.5

        spectrum = test_spec_base.get_spectrum('nm')

        self.assertEqual(spectrum[1,5],0.5)

    def test_mul_spectrum(self):
        init_wl = np.linspace(300, 500, num=10)
        init_spec = np.ones(init_wl.shape)

        mulp_wl=np.linspace(200,600,num=10)
        mulp_spec=np.ones(init_wl.shape)*0.5

        test_spec_base = Spectrum(init_wl, init_spec, 'nm', is_photon_flux=False)
        mulp_spec_base=Spectrum(mulp_wl,mulp_spec,'nm',is_photon_flux=False)
        test_spec_base=test_spec_base*mulp_spec_base

        spec_arr=test_spec_base.get_spectrum('nm')

        self.assertEqual(spec_arr[1,5],0.5)







if __name__ == '__main__':
    unittest.main()