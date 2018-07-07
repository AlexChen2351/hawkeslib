import unittest as ut
import numpy as np
from ..model.poisson import PoissonProcess, BayesianPoissonProcess
from cmath import log

from scipy.optimize import fmin
from scipy.stats import mode


class PoissonTests(ut.TestCase):

    def setUp(self):
        self.pp = PoissonProcess()
        self.a = np.array([1., 2., 3., 5.])  # simple fixture

    def test_likelihood_pars_ok(self):
        # with T
        comp = self.pp.log_likelihood_with_params(self.a, 5., 6.)
        true = - 5 * 6. + 4 * log(5.)

        self.assertAlmostEqual(comp, true)

    def test_likelihood_noT(self):
        comp = self.pp.log_likelihood_with_params(self.a, 5.)
        true = - 5.**2 + 4 * log(5.)

        self.assertAlmostEqual(comp, true)

    def test_fit(self):
        self.pp.fit(self.a)
        self.assertAlmostEqual(self.pp._mu, .8)


class BayesianPoissonTests(ut.TestCase):

    def setUp(self):
        self.pp = BayesianPoissonProcess((2., 2.))
        self.a = [4., 5., 7., 9., 20.]
        self.T = 22.

    def test_log_posterior(self):
        logpot = self.pp._get_log_posterior_pot(self.a, self.T, self.pp.mu_hyp)

        self.assertAlmostEqual(logpot(5.), -104.22966688651529)

    def test_map_fit(self):
        logpot = self.pp._get_log_posterior_pot(self.a, self.T, self.pp.mu_hyp)

        # fmin
        res = fmin(lambda x: -logpot(x), 1.)

        # analytical
        self.pp.fit(self.a, self.T)
        mu_fit = self.pp.get_params()

        self.assertAlmostEqual(res[0], mu_fit, places=4)
