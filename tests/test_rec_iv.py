__author__ = 'kanhua'

import unittest
from pypvcell.spectrum import Spectrum
from pypvcell.photocurrent import gen_step_qe
from pypvcell.ivsolver import calculate_j01_from_qe, \
    calculate_j01, calculate_bed,gen_rec_iv,\
    gen_rec_iv_by_rad_eta,one_diode_v_from_i
import numpy as np
import matplotlib.pyplot as plt
import scipy.constants as sc

class MyTestCase(unittest.TestCase):
    def test_gen_rec_iv_from_qe(self):
        """
        Compare the J01 calculated by
        1) calculate_j01_from_qe with unity QE with band edge Eg, the unityQE is generated "manually"
        2) calculate_j01() with band edge Eg
        """

        band_edge = 0.8

        unity_eqe = gen_step_qe(band_edge, 1)

        a = calculate_j01_from_qe(unity_eqe)

        b = calculate_j01(band_edge, 300, 1)

        # print(a)
        # print(b)

        assert np.isclose(a, b)

        test_v = 1.4

        exp_term = np.exp(sc.e * test_v / (sc.k * 300))

        # print(a*exp_term)
        # print(b*exp_term)

        assert np.isclose(a, b)


    def test_gen_rec_iv_from_qe_2(self):
        """
        Compare the J01 calculated by
        1) calculate_j01_from_qe with unity QE with band edge Eg, the unity QE is generated by gen_square_qe
        2) calculate_j01() with band edge Eg
        """

        test_eg=1.1
        qe = gen_step_qe(test_eg, 1, wl_bound=(0.01, 5))

        j0a = calculate_j01_from_qe(qe)
        j0b = calculate_j01(test_eg, 300, 1)

        assert np.isclose(j0a, j0b)

        print("j01 from absorptivity: %s"%j0a)
        print("j01 from band gap: %s"%j0b)


        print("testing the IV from -0.5V to 1V,with jsc=300....")
        test_voltage = np.linspace(-0.5, 1, num=10)

        va,ia=gen_rec_iv(j0a,0,1,2,300,1e10,test_voltage,jsc=300)

        vb,ib=gen_rec_iv(j0b,0,1,2,300,1e10,test_voltage,jsc=300)

        rtol=1e-2
        assert np.all(np.isclose(ia,ib,rtol=rtol))
        print("passed the I-V test, the error is within %s"%rtol)

    def test_i_from_v(self):

        j01=calculate_j01(1.42,300,1)

        # large negative voltage values introduces larger numerical error
        volt=np.linspace(-0.5,1.2,num=100)

        v,j=gen_rec_iv_by_rad_eta(j01,rad_eta=0.8,n1=1,temperature=300,rshunt=np.inf,voltage=volt)

        iv_v=one_diode_v_from_i(j,j01=j01,rad_eta=0.8,n1=1,temperature=300,jsc=0)

        print(np.max(np.abs(iv_v-v)))
        self.assertTrue(np.allclose(volt,iv_v,atol=1e-9))
        #plt.plot(iv_v-v)
        #plt.show()


    def test_diff(self):
        j01=calculate_j01(1.42,300,1)

        # large negative voltage values introduces larger numerical error
        volt=np.linspace(-0.5,1,num=100)

        v,j=gen_rec_iv_by_rad_eta(j01,rad_eta=0.8,n1=1,temperature=300,rshunt=np.inf,voltage=volt,jsc=100)

        dp=np.gradient(v*j,v[1]-v[0])
        print(v[np.argmin(v*j)])
        plt.plot(v,dp,'.')

        plt.show()



def plot_calculate_bed():
        qe_wl = np.array([1.1, 5])
        qe_qe = np.array([1, 1])

        unity_eqe = Spectrum(qe_wl,qe_qe,x_unit='eV')

        qe = gen_step_qe(1.1, 1, qe_below_edge=0)

        x1, y1 = calculate_bed(qe)
        x2, y2 = calculate_bed(unity_eqe)

        plt.semilogy(x1, y1, hold=True, label='gen_sq_qe')
        plt.semilogy(x2, y2, label="manual")
        plt.close()



if __name__ == '__main__':
    unittest.main()


