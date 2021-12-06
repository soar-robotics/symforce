import math
import numpy as np

import cc_sym as so
import sym

from symforce import typing as T
from symforce.test_util import TestCase

from lcmtypes.sym._key_t import key_t
from lcmtypes.sym._index_entry_t import index_entry_t
from lcmtypes.sym._index_t import index_t
from lcmtypes.sym._linearized_dense_factor_t import linearized_dense_factor_t
from lcmtypes.sym._optimization_iteration_t import optimization_iteration_t
from lcmtypes.sym._optimization_stats_t import optimization_stats_t
from lcmtypes.sym._optimizer_params_t import optimizer_params_t
from lcmtypes.sym._values_t import values_t


class SymforceCCSymTest(TestCase):
    """
    Test cc_sym.
    """

    def test_key(self) -> None:
        """
        Tests:
            cc_sym.Key
        """
        with self.subTest(msg="Two keys with the same fields are equal"):
            self.assertEqual(so.Key("a"), so.Key("a"))
            self.assertEqual(so.Key("a", 1), so.Key("a", 1))
            self.assertEqual(so.Key("a", 1, 2), so.Key("a", 1, 2))

        with self.subTest(msg="A key can be specified with keyword arguments"):
            self.assertEqual(so.Key("a"), so.Key(letter="a"))
            self.assertEqual(so.Key("a", 1), so.Key(letter="a", sub=1))
            self.assertEqual(so.Key("a", 1, 2), so.Key(letter="a", sub=1, super=2))

        with self.subTest(msg="Accessors correctly return the fields"):
            key = so.Key("a", 1, 2)
            self.assertEqual(key.letter, "a")
            self.assertEqual(key.sub, 1)
            self.assertEqual(key.super, 2)

        with self.subTest(msg="static method with_super works as intended"):
            letter = "a"
            sub = 1
            superscript = 2
            key_base = so.Key(letter=letter, sub=sub)
            key_with_super = so.Key.with_super(key=key_base, super=superscript)
            self.assertEqual(key_with_super.letter, letter)
            self.assertEqual(key_with_super.sub, sub)
            self.assertEqual(key_with_super.super, superscript)

        letter_sub_super_samples: T.List[
            T.Union[T.Tuple[str], T.Tuple[str, int], T.Tuple[str, int, int]]
        ] = []
        for letter in ["a", "b"]:
            letter_sub_super_samples.append((letter,))
            for sub in [1, 2]:
                letter_sub_super_samples.append((letter, sub))
                for sup in [3, 4]:
                    letter_sub_super_samples.append((letter, sub, sup))

        with self.subTest(msg="inequality operators match that of tuples"):
            for tuple1 in letter_sub_super_samples:
                for tuple2 in letter_sub_super_samples:
                    self.assertEqual(
                        so.Key(*tuple1).lexical_less_than(so.Key(*tuple2)), tuple1 < tuple2
                    )

        with self.subTest(msg="cc_sym.Key.__hash__ is defined"):
            hash(so.Key("a"))

        with self.subTest(msg="cc_sym.Key.get_lcm_type returns a key_t"):
            self.assertIsInstance(so.Key("a").get_lcm_type(), key_t)

    def test_values(self) -> None:
        """
        Tests:
            cc_sym.Values
            cc_sym.Key
            Implicitly tests conversions of sym types:
                sym.Rot2
                sym.Rot3
                sym.Pose2
                sym.Pose3
        """
        supported_types = [T.Scalar, sym.Rot2, sym.Rot3, sym.Pose2, sym.Pose3]

        for tp in supported_types:
            with self.subTest(msg=f"Can set and retrieve {tp.__name__}"):
                values = so.Values()
                val = tp()
                values.set(so.Key("v"), val)
                self.assertEqual(values.at(so.Key("v")), val)

        with self.subTest(msg=f"Can set and at 9x9 matrices and smaller"):
            values = so.Values()
            for rows in range(1, 10):
                for cols in range(1, 10):
                    matrix = [[0] * cols] * rows
                    values.set(so.Key("l", rows, cols), matrix)
                    values.at(so.Key("l", rows, cols))

                    values.set(so.Key("a", rows, cols), np.array(matrix))
                    values.at(so.Key("a", rows, cols))

        with self.subTest(msg="at raises RuntimeError if no entry exists"):
            with self.assertRaises(RuntimeError):
                so.Values().at(so.Key("a"))

        with self.subTest(msg="set returns true no value existed yet for the key"):
            values = so.Values()
            self.assertTrue(values.set(so.Key("a"), 1))
            self.assertFalse(values.set(so.Key("a"), 2))

        with self.subTest(msg="has returns whether or not key is present in Values"):
            values = so.Values()
            key = so.Key("a")
            self.assertFalse(values.has(key))
            values.set(key, 1)
            self.assertTrue(values.has(key))

        with self.subTest(msg="test that Remove returns whether or not key to be removed existed"):
            values = so.Values()
            key = so.Key("a")
            self.assertFalse(values.remove(key))
            values.set(key, 3)
            self.assertTrue(values.remove(key))

        with self.subTest(msg="Test that remove is consistent with has"):
            values = so.Values()
            key = so.Key("a")
            values.set(key, 1)
            values.remove(key=key)
            self.assertFalse(values.has(key))

        with self.subTest(msg="num_entries returns the correct number of entries"):
            values = so.Values()
            self.assertEqual(values.num_entries(), 0)
            values.set(so.Key("a"), 1.2)
            self.assertEqual(values.num_entries(), 1)
            values.remove(so.Key("a"))
            self.assertEqual(values.num_entries(), 0)

        with self.subTest(msg="Values.empty returns true if empty and false otherwise"):
            values = so.Values()
            self.assertTrue(values.empty())
            values.set(so.Key("a"), 1)
            self.assertFalse(values.empty())

        with self.subTest("Values.keys works correctly"):
            values = so.Values()
            a = so.Key("a")
            a_1 = so.Key("a", 1)
            b = so.Key("b")
            values.set(a_1, 1)
            values.set(b, 2)
            values.set(a, 3)

            self.assertEqual([a_1, b, a], values.keys())
            self.assertEqual([a_1, b, a], values.keys(sort_by_offset=True))
            keys_false = values.keys(sort_by_offset=False)
            self.assertEqual({a, a_1, b}, set(keys_false))
            self.assertEqual(3, len(keys_false))

        with self.subTest("Values.items returns a dict[Key, index_entry_t]"):
            values = so.Values()
            a = so.Key("a")
            values.set(a, 1)
            items = values.items()
            self.assertIsInstance(items, dict)
            self.assertIn(a, items)
            self.assertIsInstance(items[a], index_entry_t)

        with self.subTest("Values.items and Values.at [index_entry_t version] work together"):
            values = so.Values()
            a = so.Key("a")
            values.set(a, 1)
            items = values.items()
            self.assertEqual(values.at(entry=items[a]), 1)

        with self.subTest("Values.data returns the correct value"):
            values = so.Values()
            values.set(so.Key("a"), 1)
            values.set(so.Key("b"), 2)
            self.assertEqual(values.data(), [1, 2])

        with self.subTest(msg="Values.create_index returns an index_t"):
            values = so.Values()
            keys = [so.Key("a", i) for i in range(10)]
            for key in keys:
                values.set(key, key.sub)
            self.assertIsInstance(values.create_index(keys=keys), index_t)

        with self.subTest(msg="Values.update_or_set works as expected"):
            key_a = so.Key("a")
            key_b = so.Key("b")
            key_c = so.Key("c")

            values_1 = so.Values()
            values_1.set(key_a, 1)
            values_1.set(key_b, 2)

            values_2 = so.Values()
            values_2.set(key_b, 3)
            values_2.set(key_c, 4)

            values_1.update_or_set(index=values_2.create_index([key_b, key_c]), other=values_2)

            self.assertEqual(values_1.at(key_a), 1)
            self.assertEqual(values_1.at(key_b), 3)
            self.assertEqual(values_1.at(key_c), 4)

        with self.subTest(msg="Values.remove_all leaves a values as empty"):
            values = so.Values()
            for i in range(4):
                values.set(so.Key("a", i), i)
            values.remove_all()
            self.assertTrue(values.empty())

        with self.subTest(msg="Test that Values.cleanup is callable and returns correct output"):
            values = so.Values()
            values.set(so.Key("a"), 1)
            values.set(so.Key("b"), 2)
            values.remove(so.Key("a"))
            self.assertEqual(values.cleanup(), 1)

        for tp in supported_types:
            with self.subTest(msg=f"Can call set as a function of index_entry_t and {tp.__name__}"):
                values = so.Values()
                a = so.Key("a")
                values.set(a, tp())
                values.set(values.items()[a], tp())

        with self.subTest(msg="Test Values.update (since index overlaod) works as expected"):
            key_a = so.Key("a")
            key_b = so.Key("b")
            key_c = so.Key("c")

            values_1 = so.Values()
            values_1.set(key_a, 1)
            values_1.set(key_b, 2)
            values_1.set(key_c, 3)

            values_2 = so.Values()
            values_2.set(key_a, 4)
            values_2.set(key_b, 5)
            values_2.set(key_c, 6)

            values_1.update(index=values_1.create_index([key_b, key_c]), other=values_2)

            self.assertEqual(values_1.at(key_a), 1)
            self.assertEqual(values_1.at(key_b), 5)
            self.assertEqual(values_1.at(key_c), 6)

        with self.subTest(msg="Test Values.update (two index overlaod) works as expected"):
            key_a = so.Key("a")
            key_b = so.Key("b")
            key_c = so.Key("c")

            values_1 = so.Values()
            values_1.set(key_a, 1)
            values_1.set(key_b, 2)
            values_1.set(key_c, 3)

            values_2 = so.Values()
            values_2.set(key_b, 4)
            values_2.set(key_c, 5)

            values_1.update(
                index_this=values_1.create_index([key_b, key_c]),
                index_other=values_2.create_index([key_b, key_c]),
                other=values_2,
            )

            self.assertEqual(values_1.at(key_a), 1)
            self.assertEqual(values_1.at(key_b), 4)
            self.assertEqual(values_1.at(key_c), 5)

        with self.subTest(msg="Test that Values.retract works roughly"):
            a = so.Key("a")
            values_1 = so.Values()
            values_1.set(a, 0)
            values_2 = so.Values()
            values_2.set(a, 0)

            values_2.retract(values_2.create_index([a]), [1], 1e-8)

            self.assertNotEqual(values_1, values_2)

        with self.subTest(msg="Test that Values.local_coordinates works roughly"):
            a = so.Key("a")
            values_1 = so.Values()
            values_1.set(a, 0)
            values_2 = so.Values()
            values_2.set(a, 10)
            self.assertEqual(
                values_2.local_coordinates(values_1, values_1.create_index([a]), 0), 10
            )

        with self.subTest(msg="Test that Values.get_lcm_type returns a values_t"):
            v = so.Values()
            v.set(so.Key("a", 1, 2), 10)
            self.assertIsInstance(v.get_lcm_type(), values_t)

        with self.subTest(msg="Test the initializer from values_t"):
            v = so.Values()
            a = so.Key("a")
            v.set(so.Key("a"), 1)
            v_copy = so.Values(v.get_lcm_type())
            self.assertTrue(v_copy.has(a))
            self.assertEqual(v_copy.at(a), v.at(a))

    @staticmethod
    def pi_residual(
        x: T.Scalar,
    ) -> T.Tuple[T.List[T.Scalar], T.List[T.Scalar], T.List[T.Scalar], T.List[T.Scalar]]:
        """
        Numerical residual function r(x) = cos(x / 2) with linearization

        Args:
            x: Scalar

        Outputs:
            res: Matrix11
            jacobian: (1x1) jacobian of res wrt arg x (1)
            hessian: (1x1) Gauss-Newton hessian for arg x (1)
            rhs: (1x1) Gauss-Newton rhs for arg x (1)
        """
        x_2 = x / 2.0
        cos = math.cos(x_2)
        sin = math.sin(x_2)
        sin_2 = (1.0 / 2.0) * sin

        # Output terms
        res = [cos]
        jacobian = [-sin_2]
        hessian = [(1.0 / 4.0) * sin ** 2]
        rhs = [-cos * sin_2]
        return res, jacobian, hessian, rhs

    def test_factor(self) -> None:
        """
        Tests:
            cc_sym.Factor
        """

        pi_key = so.Key("3", 1, 4)
        pi_factor = so.Factor(
            hessian_func=lambda values: SymforceCCSymTest.pi_residual(values.at(pi_key)),
            keys=[pi_key],
        )
        pi_jacobian_factor = so.Factor.jacobian(
            jacobian_func=lambda values: SymforceCCSymTest.pi_residual(values.at(pi_key))[0:2],
            keys=[pi_key],
        )

        with self.subTest(msg="Test that Factor.linearized_factor/linearize are wrapped"):
            pi_values = so.Values()
            eval_value = 3.0
            pi_values.set(pi_key, eval_value)
            self.assertIsInstance(pi_factor.linearized_factor(pi_values), linearized_dense_factor_t)

            residual, jacobian = pi_factor.linearize(pi_values)
            target_residual, target_jacobian, *_ = SymforceCCSymTest.pi_residual(eval_value)
            self.assertAlmostEqual(target_residual[0], residual[0])
            self.assertAlmostEqual(target_jacobian[0], jacobian[0, 0])

        with self.subTest(msg="Test that Factor.keys is wrapped"):
            self.assertEqual(pi_factor.keys(), [pi_key])

    def test_optimization_stats(self) -> None:
        """
        Tests:
            cc_sym.OptimizationStats
            cc_sym.Linearization
        """

        with self.subTest(msg="Can read and write to iterations field"):
            stats = so.OptimizationStats()
            self.assertIsInstance(stats.iterations, list)
            stats.iterations = [optimization_iteration_t() for _ in range(5)]

        with self.subTest(msg="Can read and write to best_index and early_exited"):
            stats = so.OptimizationStats()
            stats.best_index = stats.best_index
            stats.early_exited = stats.early_exited

        with self.subTest(msg="Can read and write to best_linearization"):
            stats = so.OptimizationStats()
            stats.best_linearization = None
            self.assertIsNone(stats.best_linearization)
            stats.best_linearization = so.Linearization()
            self.assertIsInstance(stats.best_linearization, so.Linearization)

        with self.subTest(msg="get_lcm_type is wrapped"):
            stats = so.OptimizationStats()
            self.assertIsInstance(stats.get_lcm_type(), optimization_stats_t)

    def test_optimizer(self) -> None:
        """
        Tests:
            cc_sym.default_optimizer_params
            cc_sym.Optimizer
            cc_sym.Linearization
        """

        with self.subTest(msg="Test that default_optimizer_params is wrapped"):
            self.assertIsInstance(so.default_optimizer_params(), optimizer_params_t)

        pi_key = so.Key("3", 1, 4)
        pi_factor = so.Factor(
            hessian_func=lambda values: SymforceCCSymTest.pi_residual(values.at(pi_key)),
            keys=[pi_key],
        )

        with self.subTest(msg="Can construct an Optimizer with or without default arguments"):
            required_args = {
                "params": so.default_optimizer_params(),
                "factors": [pi_factor],
            }
            so.Optimizer(**required_args)
            so.Optimizer(
                **required_args,
                epsilon=1e-6,
                name="OptimizeTest",
                keys=[],
                debug_stats=False,
                check_derivatives=False,
            )

        make_opt = lambda: so.Optimizer(params=so.default_optimizer_params(), factors=[pi_factor])

        with self.subTest(msg="Optimizer.optimize has been wrapped"):
            values = so.Values()
            values.set(pi_key, 3.0)

            opt = make_opt()

            # Testing the wrapping of overload
            # OptimizationStats<Scalar> Optimize(Values<Scalar>* values, int num_iterations = -1,
            #                                    bool populate_best_linearization = false);
            self.assertIsInstance(opt.optimize(values=values), so.OptimizationStats)
            self.assertAlmostEqual(values.at(pi_key), math.pi)

            self.assertIsInstance(
                opt.optimize(values=values, num_iterations=2), so.OptimizationStats
            )
            self.assertIsInstance(
                opt.optimize(values=values, populate_best_linearization=True), so.OptimizationStats
            )
            self.assertIsInstance(opt.optimize(values, 2, True), so.OptimizationStats)

            # Testing the wrapping of overload
            # void Optimize(Values<Scalar>* values, int num_iterations,
            #               bool populate_best_linearization, OptimizationStats<Scalar>* stats);
            self.assertIsNone(
                opt.optimize(
                    values=values,
                    num_iterations=2,
                    populate_best_linearization=False,
                    stats=so.OptimizationStats(),
                )
            )
            self.assertIsNone(opt.optimize(values, 2, False, so.OptimizationStats(),))

            # Testing the wrapping of overload
            # void Optimize(Values<Scalar>* values, int num_iterations,
            #               OptimizationStats<Scalar>* stats);
            self.assertIsNone(
                opt.optimize(values=values, num_iterations=2, stats=so.OptimizationStats())
            )
            self.assertIsNone(opt.optimize(values, 2, so.OptimizationStats()))

            # Testing the wrapping of overlaod
            # void Optimize(Values<Scalar>* values, OptimizationStats<Scalar>* stats);
            self.assertIsNone(opt.optimize(values=values, stats=so.OptimizationStats()))
            self.assertIsNone(opt.optimize(values, so.OptimizationStats()))

            # Testing that the passed in stats are actually modified
            stats = so.OptimizationStats()
            self.assertEqual(len(stats.iterations), 0)
            opt.optimize(values=values, stats=stats)
            self.assertNotEqual(len(stats.iterations), 0)

        with self.subTest(msg="Optimizer.linearize has been wrapped"):
            values = so.Values()
            values.set(pi_key, 2.0)
            opt = make_opt()
            self.assertIsInstance(opt.linearize(values=values), so.Linearization)

        with self.subTest(msg="The methods of Linearization have been wrapped"):
            so.Linearization()

            values = so.Values()
            values.set(pi_key, 3.0)
            opt = make_opt()
            lin = opt.linearize(values=values)

            lin.residual = lin.residual
            lin.hessian_lower = lin.hessian_lower
            lin.jacobian = lin.jacobian
            lin.rhs = lin.rhs

            lin.set_initialized()
            self.assertTrue(lin.is_initialized())
            lin.reset()
            self.assertFalse(lin.is_initialized())
            lin.set_initialized(initialized=True)
            self.assertTrue(lin.is_initialized())
            lin.set_initialized(initialized=False)
            self.assertFalse(lin.is_initialized())

            lin.set_initialized()
            self.assertIsInstance(lin.error(), T.Scalar)
            self.assertIsInstance(lin.linear_error(x_update=[0.01]), T.Scalar)
            lin.linear_error([0.01])

        with self.subTest(msg="Optimizer.compute_all_covariances has been wrapped"):
            values = so.Values()
            values.set(pi_key, 2.0)
            opt = make_opt()
            opt.optimize(values=values)
            self.assertIsInstance(
                opt.compute_all_covariances(linearization=opt.linearize(values)), dict
            )

        with self.subTest(msg="Optimizer.compute_covariances has been wrapped"):
            values = so.Values()
            values.set(pi_key, 1.0)
            opt = make_opt()
            self.assertIsInstance(
                opt.compute_covariances(linearization=opt.linearize(values), keys=[pi_key]), dict
            )

        with self.subTest(msg="Optimzer.keys is wrapped"):
            opt = make_opt()
            self.assertEqual(opt.keys(), [pi_key])

        with self.subTest(msg="Optimizer.update_params is wrapped"):
            opt = make_opt()
            opt.update_params(params=so.default_optimizer_params())

        with self.subTest(msg="cc_sym.optimize is wrapped"):
            values = so.Values()
            values.set(pi_key, 3.0)
            so.optimize(
                params=so.default_optimizer_params(),
                factors=[pi_factor],
                values=values,
                epsilon=1e-9,
            )
            self.assertAlmostEqual(values.at(pi_key), math.pi)

            so.optimize(params=so.default_optimizer_params(), factors=[pi_factor], values=values)


if __name__ == "__main__":
    TestCase.main()
