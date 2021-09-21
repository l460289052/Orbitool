import numpy as np
from numpy.polynomial import polynomial
from ...structures import BaseStructure


class PolynomialRegressionFunc(BaseStructure):
    h5_type = "polynomial regression function"

    poly_coef: np.ndarray

    @classmethod
    def FactoryFit(cls, mz: np.ndarray, rtol: np.ndarray, degree):
        poly_coef = polynomial.polyfit(mz, rtol, degree)
        return cls(poly_coef=poly_coef)

    def predictRtol(self, mz: np.ndarray):
        return polynomial.polyval(mz, self.poly_coef)

    def predictMz(self, mz: np.ndarray):
        return mz * (1 - polynomial.polyval(mz, self.poly_coef))
