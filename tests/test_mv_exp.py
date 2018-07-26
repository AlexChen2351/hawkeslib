import os
import unittest as ut
import numpy as np

from ..model.c import c_mv_exp
from .. import UnivariateExpHawkesProcess


class MVExpLikelihoodTests(ut.TestCase):

    def test_degenerate_mv_ll_matches_uv_ll(self):

        fpath = os.path.join(os.path.dirname(__file__), 'tfx_fixture.npy')
        arr = np.load(fpath)

        uv = UnivariateExpHawkesProcess()
        uv.set_params(5, .2, 10.)
        uvll = uv.log_likelihood(arr, arr[-1])

        mvll = c_mv_exp.mv_exp_ll(arr, np.zeros(len(arr), dtype=np.int),
                                  np.ones(1) * 5,
                                  np.ones((1, 1)) * .2, 10., arr[-1])

        self.assertAlmostEqual(uvll, mvll, places=3)

    def test_mv_ll_matches_naive(self):
        N = 100
        fpath = os.path.join(os.path.dirname(__file__), 'tfx_fixture.npy')
        t = np.load(fpath)[:N]
        c = np.random.choice([0,1,2], size=N)

        K = 3
        mu = np.random.rand(K)
        A = np.random.rand(K, K) * .05 + np.eye(K) * .3
        theta = 1.

        T = t[-1]

        # compute log likelihood naively
        ll = -np.sum(mu) * T
        F = np.zeros(K)
        for i in range(N):
            z = mu[c[i]]
            for j in range(i):
                z += A[c[j], c[i]] * theta * np.exp(-theta * (t[i] - t[j]))
            ll += np.log(z)
            F[c[i]] += 1 - np.exp(-theta * (T - t[i]))
        ll -= A.T.dot(F).sum()

        ll_lib = c_mv_exp.mv_exp_ll(t, c, mu, A, theta, T)

        self.assertAlmostEqual(ll, ll_lib, places=4)


class MVExpBranchingSamplerTests(ut.TestCase):

    def setUp(self):
        pass

    def test_mv_sample_diag_kernel_numbers_ok(self):
        K, T = 3, 10000
        mu = np.array([.5, .3, .2])
        A = np.eye(K) * .2
        # A[2, 0] = .5
        theta = 1.

        tres, cres = c_mv_exp.mv_exp_sample_branching(T, mu, A, theta)

        # calculate expectation
        I_K = np.eye(A.T.shape[0])
        Endt = np.linalg.pinv(I_K - A.T).dot(mu) * T  # expected number of each mark
        Rndt = np.bincount(cres)  # true outcomes

        devi = np.abs(Endt - Rndt) / Rndt

        self.assertLessEqual(max(devi), .1)  # max deviation should be less than 0.1

    def test_mv_sample_full_kernel_numbers_ok(self):
        K, T = 3, 10000
        mu = np.array([.5, .3, .2])
        A = np.eye(K) * .2
        A[2, 0] = .5
        A[0, 1] = .3

        theta = 1.

        tres, cres = c_mv_exp.mv_exp_sample_branching(T, mu, A, theta)

        # calculate expectation
        I_K = np.eye(A.T.shape[0])
        Endt = np.linalg.pinv(I_K - A.T).dot(mu) * T  # expected number of each mark
        Rndt = np.bincount(cres)  # true outcomes

        devi = np.abs(Endt - Rndt) / Rndt

        self.assertLessEqual(max(devi), .1)  # max deviation should be less than 0.1

    def test_uv_sample_matches_numbers(self):
        K, T = 1, 10000
        mu = np.array([.5])
        A = np.eye(K) * .2
        theta = 1.

        tres, cres = c_mv_exp.mv_exp_sample_branching(T, mu, A, theta)
        Endt = np.bincount(cres)[0]

        uv = UnivariateExpHawkesProcess()
        uv.set_params(mu[0], .2, 1.)
        Rndt = len(uv.sample(T))

        devi = np.abs(Endt - Rndt) / Rndt

        self.assertLessEqual(devi, .1)

    def test_mv_sample_diag_kernel_uv_matches_numbers(self):
        K, T = 2, 10000
        mu = np.array([.5, .3])
        A = np.eye(K) * .3
        theta = 1.

        tres, cres = c_mv_exp.mv_exp_sample_branching(T, mu, A, theta)
        Endt = np.bincount(cres)[0]

        uv = UnivariateExpHawkesProcess()
        uv.set_params(mu[0], .2, 1.)
        Rndt = len(uv.sample(T))

        devi = np.abs(Endt - Rndt) / Rndt

        self.assertLessEqual(devi, .1)


class MVEMAlgorithmTests(ut.TestCase):

    def setUp(self):

        self.t = np.load(os.path.join(os.path.dirname(__file__), 'tfx_mvt.npy'))
        self.c = np.load(os.path.join(os.path.dirname(__file__), 'tfx_mvc.npy'))
        self.T = self.t[-1]

    def test_em_runs_no_convergence_issue(self):

        try:
            c_mv_exp.mv_exp_fit_em(self.t, self.c, self.T, maxiter=100)
        except Exception as e:
            if "convergence" in e.message:
                self.fail(e.message)

    def test_em_runs_params_close(self):

        _, p, _ = c_mv_exp.mv_exp_fit_em(self.t, self.c, self.T, maxiter=200, reltol=1e-6)

        assert np.allclose(np.array([.2, .6]), p[0], rtol=0.2), p[0]
        assert np.allclose(np.eye(2) * .4 + np.ones((2,2)) * .1, p[1], rtol=0.2)
        self.assertAlmostEqual(1., p[2], delta=.2)
